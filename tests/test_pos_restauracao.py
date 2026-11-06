"""Restaurar um backup não pode devolver acessos revogados depois dele.

Regressão do achado #6 de security-audit/NEEDS-VALIDATION.md: o banco
restaurado traz de volta sessões encerradas, contas desativadas, senhas e
MFA redefinidos e papéis rebaixados. As defesas são a época de revogação
fora do banco (SESSOES_VALIDAS_DESDE) e o scripts.pos_restauracao.

A "restauração" é simulada na transação do teste: guarda as linhas do
usuário e das sessões dele (o snapshot) e depois as regrava como estavam.
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.models.usuario import AuditLog, SessaoUsuario, Usuario
from scripts.pos_restauracao import (
    Acesso,
    aplicar,
    decidir,
    ler_acessos,
    listar_auditoria,
)
from tests.conftest import SENHA_BOA


def _id(db: Session, nome: str) -> int:
    return db.scalar(select(Usuario.id).where(Usuario.nome == nome))


def _login(client_anon: TestClient, nome: str, senha: str = SENHA_BOA):
    return client_anon.post(
        "/api/v1/auth/login", data={"username": nome, "password": senha}
    )


def _me(client_anon: TestClient, headers: dict[str, str]) -> int:
    return client_anon.get("/api/v1/auth/me", headers=headers).status_code


def _snapshot(db: Session, usuario_id: int) -> tuple[dict, list[dict]]:
    usuario = (
        db.execute(text("SELECT * FROM usuario WHERE id = :id"), {"id": usuario_id})
        .mappings()
        .one()
    )
    sessoes = (
        db.execute(
            text("SELECT * FROM sessao_usuario WHERE usuario_id = :id"),
            {"id": usuario_id},
        )
        .mappings()
        .all()
    )
    return dict(usuario), [dict(s) for s in sessoes]


def _restaurar(db: Session, snapshot: tuple[dict, list[dict]]) -> None:
    """Põe o usuário e as sessões dele de volta como estavam no snapshot."""
    usuario, sessoes = snapshot
    colunas = ", ".join(f"{c} = :{c}" for c in usuario if c != "id")
    db.execute(text(f"UPDATE usuario SET {colunas} WHERE id = :id"), usuario)
    db.execute(
        text("DELETE FROM sessao_usuario WHERE usuario_id = :id"), {"id": usuario["id"]}
    )
    for sessao in sessoes:
        nomes = ", ".join(sessao)
        valores = ", ".join(f":{c}" for c in sessao)
        db.execute(
            text(f"INSERT INTO sessao_usuario ({nomes}) VALUES ({valores})"), sessao
        )
    db.expire_all()


def _rodar_script(db: Session, antigo: dict | None) -> list[tuple[str, str]]:
    acoes = decidir(ler_acessos(db), antigo)
    senhas = aplicar(db, acoes, agora=datetime.now(UTC))
    db.flush()
    db.expire_all()
    return senhas


# ---------- SESSOES_VALIDAS_DESDE ----------


def test_token_emitido_antes_da_epoca_e_recusado(
    client_anon: TestClient, entrar_como, monkeypatch
):
    headers = entrar_como("Antes Da Epoca")
    assert _me(client_anon, headers) == 200

    monkeypatch.setattr(
        settings, "SESSOES_VALIDAS_DESDE", datetime.now(UTC) + timedelta(seconds=2)
    )
    assert _me(client_anon, headers) == 401

    # época no passado: o mesmo token vale
    monkeypatch.setattr(
        settings, "SESSOES_VALIDAS_DESDE", datetime.now(UTC) - timedelta(hours=1)
    )
    assert _me(client_anon, headers) == 200


def test_token_sem_iat_e_recusado(client_anon: TestClient, db: Session, entrar_como):
    headers = entrar_como("Sem Iat")
    token = headers["Authorization"].removeprefix("Bearer ")
    payload = jwt.decode(token, options={"verify_signature": False})
    del payload["iat"]
    sem_iat = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert _me(client_anon, {"Authorization": f"Bearer {sem_iat}"}) == 401


def test_config_da_epoca():
    base = {"DATABASE_URL": "postgresql://x@localhost/x"}
    assert Settings(**base, SESSOES_VALIDAS_DESDE="").SESSOES_VALIDAS_DESDE is None
    sem_fuso = Settings(**base, SESSOES_VALIDAS_DESDE="2026-11-06T10:00:00")
    assert sem_fuso.SESSOES_VALIDAS_DESDE == datetime(2026, 11, 6, 10, tzinfo=UTC)
    with pytest.raises(ValidationError, match="futuro"):
        Settings(**base, SESSOES_VALIDAS_DESDE=datetime.now(UTC) + timedelta(days=1))


# ---------- o cenário do relatório, com e sem o script ----------


def test_restaurar_ressuscita_conta_desativada_e_o_script_corrige(
    client: TestClient, client_anon: TestClient, db: Session, entrar_como
):
    token = entrar_como("Ciclano Teste")
    uid = _id(db, "Ciclano Teste")
    snapshot = _snapshot(db, uid)

    r = client.patch(f"/api/v1/usuarios/{uid}", json={"ativo": False})
    assert r.status_code == 200
    assert _me(client_anon, token) == 401
    antigo = ler_acessos(db)  # o banco de antes da restauração

    _restaurar(db, snapshot)
    assert _me(client_anon, token) == 200  # o defeito: o acesso voltou

    senhas = _rodar_script(db, antigo)
    assert "Ciclano Teste" not in dict(senhas)
    assert _me(client_anon, token) == 401
    assert _login(client_anon, "Ciclano Teste").status_code == 401
    assert db.get(Usuario, uid).ativo is False


def test_senha_redefinida_depois_do_backup_nao_volta_a_valer(
    client: TestClient, client_anon: TestClient, db: Session, entrar_como
):
    token = entrar_como("Senha Vazada")
    uid = _id(db, "Senha Vazada")
    snapshot = _snapshot(db, uid)
    client.post(f"/api/v1/usuarios/{uid}/redefinir-senha")
    antigo = ler_acessos(db)

    _restaurar(db, snapshot)
    assert _login(client_anon, "Senha Vazada").status_code == 200  # o defeito

    senhas = dict(_rodar_script(db, antigo))
    assert _me(client_anon, token) == 401
    assert _login(client_anon, "Senha Vazada").status_code == 401
    r = _login(client_anon, "Senha Vazada", senhas["Senha Vazada"])
    assert r.status_code == 200
    assert r.json()["pendencias"] == ["trocar_senha"]


def test_admin_rebaixado_depois_do_backup_continua_operador(
    client: TestClient, db: Session, entrar_como
):
    entrar_como("Ex Admin", papel="admin")
    uid = _id(db, "Ex Admin")
    snapshot = _snapshot(db, uid)
    client.patch(f"/api/v1/usuarios/{uid}", json={"papel": "operador"})
    antigo = ler_acessos(db)

    _restaurar(db, snapshot)
    assert db.get(Usuario, uid).papel.value == "admin"  # o defeito

    _rodar_script(db, antigo)
    assert db.get(Usuario, uid).papel.value == "operador"


def test_sem_banco_antigo_todo_mundo_refaz_o_acesso(
    client_anon: TestClient, db: Session, entrar_como
):
    token = entrar_como("Perda Total")
    senhas = dict(_rodar_script(db, None))

    assert _me(client_anon, token) == 401
    assert _login(client_anon, "Perda Total").status_code == 401
    assert _login(client_anon, "Perda Total", senhas["Perda Total"]).status_code == 200
    ativos = db.scalars(select(Usuario.nome).where(Usuario.ativo.is_(True))).all()
    assert set(senhas) == set(ativos)
    assert all(
        not u.mfa_ativo for u in db.scalars(select(Usuario).where(Usuario.ativo))
    )


def test_script_revoga_todas_as_sessoes_e_registra_na_auditoria(
    db: Session, entrar_como
):
    entrar_como("Qualquer Um")
    antes = datetime.now(UTC) - timedelta(minutes=1)
    _rodar_script(db, ler_acessos(db))  # nada mudou: ninguém troca de senha

    abertas = db.scalar(
        select(func.count())
        .select_from(SessaoUsuario)
        .where(SessaoUsuario.revogada_em.is_(None))
    )
    assert abertas == 0
    registro = db.scalars(
        select(AuditLog).where(AuditLog.dados["pos_restauracao"].as_boolean())
    ).one()
    assert registro.dados["senhas_novas"] == 0
    assert any(
        linha.dados and linha.dados.get("pos_restauracao")
        for linha in listar_auditoria(db, antes)
    )


# ---------- a regra do mais restritivo ----------


def _acesso(**mudancas) -> Acesso:
    base = {
        "id": 1,
        "nome": "Fulana",
        "ativo": True,
        "papel": "admin",
        "senha_hash": "hash-1",
        "mfa_ativo": True,
        "mfa_segredo": b"cifrado-1",
    }
    return Acesso(**{**base, **mudancas})


@pytest.mark.parametrize(
    ("restaurado", "antigo", "esperado"),
    [
        (_acesso(), _acesso(), None),
        (_acesso(), _acesso(ativo=False), {"desativar": True, "nova_senha": False}),
        (_acesso(), _acesso(papel="operador"), {"rebaixar": True, "nova_senha": False}),
        (_acesso(papel="operador"), _acesso(), None),  # promovido depois: fica o menor
        (_acesso(), _acesso(senha_hash="hash-2"), {"nova_senha": True}),
        (_acesso(), _acesso(mfa_ativo=False, mfa_segredo=None), {"nova_senha": True}),
        (_acesso(), _acesso(mfa_segredo=b"cifrado-2"), {"nova_senha": True}),
        (_acesso(ativo=False), _acesso(senha_hash="hash-2"), None),
        (_acesso(), None, {"nova_senha": True}),  # não existe no antigo
    ],
)
def test_decidir_aplica_o_mais_restritivo(restaurado, antigo, esperado):
    acoes = decidir({1: restaurado}, {1: antigo} if antigo else {})
    if esperado is None:
        assert acoes == []
    else:
        (acao,) = acoes
        for campo, valor in esperado.items():
            assert getattr(acao, campo) is valor, campo
