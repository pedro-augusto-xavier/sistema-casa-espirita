"""Época de credencial: sessão aberta com a senha/MFA/papel de antes não vale.

Regressão do achado #5 de security-audit/NEEDS-VALIDATION.md: um login que
lia a senha antiga e gravava a sessão DEPOIS do UPDATE de revogar_todas
escapava da revogação (a troca de senha ou a ativação do MFA não derrubava
o atacante).

A corrida é simulada de forma determinística: a mudança da vítima roda no
meio do login, entre a conferência da senha e a abertura da sessão (no
gancho crud_sessao.limpar_antigas, chamado logo antes de abrir). Um teste
com threads e conexões separadas exigiria commitar usuários no banco local,
e a auditoria imutável não deixa apagá-los depois.
"""

from datetime import UTC, datetime, timedelta

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import criar_token_sessao
from app.crud import sessao as crud_sessao
from app.crud import usuario as crud_usuario
from app.models.usuario import SessaoUsuario, Usuario
from tests.conftest import SENHA_BOA

SENHA_NOVA = "cafe-com-bolo-de-fuba"


def _usuario(db: Session, nome: str) -> Usuario:
    return db.scalar(select(Usuario).where(Usuario.nome == nome))


def _outra_sessao(db: Session, nome: str) -> dict[str, str]:
    """Uma segunda sessão da mesma pessoa (outro aparelho)."""
    token = crud_sessao.abrir(db, _usuario(db, nome))
    return {"Authorization": f"Bearer {token}"}


def _vale(client_anon: TestClient, headers: dict[str, str]) -> bool:
    r = client_anon.get("/api/v1/pessoas", headers=headers)
    assert r.status_code in (200, 401), r.text
    return r.status_code == 200


def _login(client_anon: TestClient, nome: str, senha: str = SENHA_BOA):
    return client_anon.post(
        "/api/v1/auth/login", data={"username": nome, "password": senha}
    )


def _ativar_mfa(client_anon: TestClient, headers: dict[str, str]) -> None:
    segredo = client_anon.post("/api/v1/auth/mfa/iniciar", headers=headers).json()[
        "segredo"
    ]
    r = client_anon.post(
        "/api/v1/auth/mfa/ativar",
        json={"codigo": pyotp.TOTP(segredo).now()},
        headers=headers,
    )
    assert r.status_code == 204, r.text


# ---------- a corrida do relatório ----------


@pytest.fixture()
def mudanca_no_meio_do_login(monkeypatch):
    """mudanca_no_meio_do_login(funcao): `funcao` roda uma vez, no meio do
    próximo login, depois de a senha (e o MFA) ter sido conferida e antes de
    a sessão ser gravada."""

    def _agendar(funcao):
        original = crud_sessao.limpar_antigas
        feito = []

        def _gancho(db):
            if not feito:
                feito.append(True)
                funcao()
            original(db)

        monkeypatch.setattr(crud_sessao, "limpar_antigas", _gancho)

    return _agendar


def test_login_que_leu_a_senha_antiga_nao_sobrevive_a_troca_de_senha(
    client_anon: TestClient, db: Session, entrar_como, mudanca_no_meio_do_login
):
    vitima = entrar_como("Vitima Corrida")
    sessao_vitima = db.scalar(
        select(SessaoUsuario).where(
            SessaoUsuario.usuario_id == _usuario(db, "Vitima Corrida").id
        )
    )

    def _vitima_troca_a_senha():
        crud_usuario.trocar_senha_propria(
            db,
            _usuario(db, "Vitima Corrida"),
            SENHA_NOVA,
            sessao_atual=sessao_vitima,
        )

    mudanca_no_meio_do_login(_vitima_troca_a_senha)
    r = _login(client_anon, "Vitima Corrida")  # atacante com a senha vazada
    assert r.status_code == 401, r.text
    assert r.json()["detail"]["codigo"] == "credenciais_mudaram"

    # só sobrou a sessão da vítima, que continua valendo
    ids = db.scalars(
        select(SessaoUsuario.id).where(
            SessaoUsuario.usuario_id == _usuario(db, "Vitima Corrida").id
        )
    ).all()
    assert ids == [sessao_vitima.id]
    assert _vale(client_anon, vitima)


def test_login_sem_codigo_nao_sobrevive_a_ativacao_do_mfa(
    client_anon: TestClient, db: Session, entrar_como, mudanca_no_meio_do_login
):
    entrar_como("Vitima Mfa")

    def _vitima_liga_o_mfa():
        usuario = _usuario(db, "Vitima Mfa")
        usuario.mfa_segredo = pyotp.random_base32()
        usuario.mfa_ativo = True
        crud_usuario.credencial_mudou(db, usuario)

    mudanca_no_meio_do_login(_vitima_liga_o_mfa)
    # o login leu mfa_ativo=false e não pediu código
    r = _login(client_anon, "Vitima Mfa")
    assert r.status_code == 401, r.text
    assert r.json()["detail"]["codigo"] == "credenciais_mudaram"


def test_login_nao_abre_sessao_de_conta_desativada_no_meio(
    client_anon: TestClient, db: Session, entrar_como, mudanca_no_meio_do_login
):
    entrar_como("Desligada No Meio")

    def _admin_desativa():
        usuario = _usuario(db, "Desligada No Meio")
        usuario.ativo = False
        db.commit()

    mudanca_no_meio_do_login(_admin_desativa)
    assert _login(client_anon, "Desligada No Meio").status_code == 401


def test_sessao_gravada_com_a_epoca_antiga_nao_vale(
    client_anon: TestClient, db: Session, entrar_como
):
    """O sink do relatório, sem depender da reconferência do login: mesmo
    que a sessão seja gravada depois da troca de senha (criada_em mais nova
    que senha_alterada_em), ela carrega a época lida antes e é recusada."""
    vitima = entrar_como("Vitima Sink")
    usuario = _usuario(db, "Vitima Sink")
    epoca_lida = usuario.epoca_credencial

    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": SENHA_BOA, "senha_nova": SENHA_NOVA},
        headers=vitima,
    )
    assert r.status_code == 204, r.text

    agora = datetime.now(UTC)
    atrasada = SessaoUsuario(
        id="sessao-gravada-depois-da-revogacao",
        usuario_id=usuario.id,
        criada_em=agora,
        expira_em=agora + timedelta(hours=8),
        epoca_credencial=epoca_lida,
    )
    db.add(atrasada)
    db.flush()
    assert atrasada.criada_em > usuario.senha_alterada_em
    token = criar_token_sessao(usuario.id, atrasada.id, atrasada.expira_em)
    headers = {"Authorization": f"Bearer {token}"}

    assert client_anon.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 401
    assert _vale(client_anon, vitima)


# ---------- quem cai e quem continua ----------


def test_trocar_a_propria_senha_derruba_as_outras_e_mantem_a_atual(
    client_anon: TestClient, db: Session, entrar_como
):
    atual = entrar_como("Troca Senha")
    outra = _outra_sessao(db, "Troca Senha")
    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": SENHA_BOA, "senha_nova": SENHA_NOVA},
        headers=atual,
    )
    assert r.status_code == 204, r.text
    assert _vale(client_anon, atual)
    assert not _vale(client_anon, outra)


def test_ativar_mfa_derruba_as_outras_e_mantem_a_atual(
    client_anon: TestClient, db: Session, entrar_como
):
    atual = entrar_como("Liga Mfa")
    outra = _outra_sessao(db, "Liga Mfa")
    _ativar_mfa(client_anon, atual)
    assert _vale(client_anon, atual)
    assert not _vale(client_anon, outra)


def test_desativar_o_proprio_mfa_derruba_as_outras_e_mantem_a_atual(
    client_anon: TestClient, db: Session, entrar_como
):
    atual = entrar_como("Desliga Mfa")
    _ativar_mfa(client_anon, atual)
    outra = _outra_sessao(db, "Desliga Mfa")
    r = client_anon.post(
        "/api/v1/auth/mfa/desativar", json={"senha": SENHA_BOA}, headers=atual
    )
    assert r.status_code == 204, r.text
    assert _vale(client_anon, atual)
    assert not _vale(client_anon, outra)


@pytest.mark.parametrize(
    "acao",
    [
        lambda c, uid: c.post(f"/api/v1/usuarios/{uid}/redefinir-senha"),
        lambda c, uid: c.post(f"/api/v1/usuarios/{uid}/resetar-mfa"),
        lambda c, uid: c.patch(f"/api/v1/usuarios/{uid}", json={"papel": "admin"}),
    ],
    ids=["redefinir-senha", "resetar-mfa", "mudar-papel"],
)
def test_admin_mudando_a_credencial_derruba_todas(
    client: TestClient, client_anon: TestClient, db: Session, entrar_como, acao
):
    uma = entrar_como("Alvo Do Admin")
    outra = _outra_sessao(db, "Alvo Do Admin")
    r = acao(client, _usuario(db, "Alvo Do Admin").id)
    assert r.status_code == 200, r.text
    assert not _vale(client_anon, uma)
    assert not _vale(client_anon, outra)


def test_editar_sem_mudar_o_papel_nao_derruba(
    client: TestClient, client_anon: TestClient, db: Session, entrar_como
):
    sessao = entrar_como("Continua Operador")
    uid = _usuario(db, "Continua Operador").id
    r = client.patch(f"/api/v1/usuarios/{uid}", json={"papel": "operador"})
    assert r.status_code == 200, r.text
    assert _vale(client_anon, sessao)
