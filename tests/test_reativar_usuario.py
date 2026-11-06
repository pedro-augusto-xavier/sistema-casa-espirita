"""Reativar usuário gera senha provisória nova; a senha de antes não volta.

Regressão do achado #2 de security-audit/NEEDS-VALIDATION.md: o backfill da
migração 0adbab7209a9 só marcou senha provisória em quem estava ativo. Uma
conta desativada antes dela ficava com a senha antiga (ex.: 8 números do CPF)
e, ao ser reativada pelo admin, entrava com ela sem pendência nenhuma.
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_senha
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario

SENHA_ANTIGA = "39053344"  # 8 números de CPF, como a tela antiga sugeria


def _inativo_de_antes_da_migracao(
    db: Session, nome: str, papel: str = "operador"
) -> Usuario:
    """Conta no estado que o backfill deixou: desativada, senha antiga, nunca
    marcada como provisória e sem senha_alterada_em."""
    usuario = Usuario(
        nome=nome,
        senha_hash=hash_senha(SENHA_ANTIGA),
        papel=PapelUsuario(papel),
        ativo=False,
        senha_provisoria=False,
        senha_alterada_em=None,
    )
    db.add(usuario)
    db.flush()
    return usuario


def _login(client_anon: TestClient, nome: str, senha: str):
    return client_anon.post(
        "/api/v1/auth/login", data={"username": nome, "password": senha}
    )


def test_reativar_troca_a_senha_antiga_por_uma_provisoria_gerada(
    client: TestClient, client_anon: TestClient, db: Session
):
    alvo = _inativo_de_antes_da_migracao(db, "Beltrano Inativo")
    antes = datetime.now(UTC)

    r = client.post(f"/api/v1/usuarios/{alvo.id}/reativar")
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["ativo"] is True
    assert corpo["senha_provisoria"] is True
    nova = corpo["senha_gerada"]
    assert len(nova) >= 16 and nova != SENHA_ANTIGA
    expira = datetime.fromisoformat(corpo["senha_expira_em"])
    assert abs(expira - (antes + timedelta(hours=72))) < timedelta(minutes=1)

    # a senha de antes da desativação não entra mais
    assert _login(client_anon, "Beltrano Inativo", SENHA_ANTIGA).status_code == 401

    login = _login(client_anon, "Beltrano Inativo", nova)
    assert login.status_code == 200, login.text
    assert login.json()["pendencias"] == ["trocar_senha"]
    token = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client_anon.get("/api/v1/pessoas", headers=token).status_code == 403


def test_admin_reativado_tem_que_trocar_senha_e_configurar_mfa(
    client: TestClient, client_anon: TestClient, db: Session
):
    alvo = _inativo_de_antes_da_migracao(db, "Admin Inativo", papel="admin")
    nova = client.post(f"/api/v1/usuarios/{alvo.id}/reativar").json()["senha_gerada"]

    assert _login(client_anon, "Admin Inativo", SENHA_ANTIGA).status_code == 401
    login = _login(client_anon, "Admin Inativo", nova)
    assert login.status_code == 200, login.text
    assert login.json()["pendencias"] == ["trocar_senha", "configurar_mfa"]


def test_patch_nao_reativa(client: TestClient, client_anon: TestClient, db: Session):
    alvo = _inativo_de_antes_da_migracao(db, "Reativa Por Patch")

    r = client.patch(f"/api/v1/usuarios/{alvo.id}", json={"ativo": True})
    assert r.status_code == 422

    db.refresh(alvo)
    assert alvo.ativo is False
    assert _login(client_anon, "Reativa Por Patch", SENHA_ANTIGA).status_code == 401


def test_patch_continua_desativando(
    client: TestClient, client_anon: TestClient, entrar_como
):
    headers = entrar_como("Vai Sair")
    eu = client_anon.get("/api/v1/auth/me", headers=headers).json()

    r = client.patch(f"/api/v1/usuarios/{eu['id']}", json={"ativo": False})
    assert r.status_code == 200, r.text
    assert r.json()["ativo"] is False
    assert client_anon.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_reativar_quem_ja_esta_ativo_e_recusado(
    client: TestClient, client_anon: TestClient, entrar_como
):
    headers = entrar_como("Ja Ativo")
    eu = client_anon.get("/api/v1/auth/me", headers=headers).json()

    r = client.post(f"/api/v1/usuarios/{eu['id']}/reativar")
    assert r.status_code == 422
    # nada mudou: a sessão e a senha dele continuam valendo
    assert client_anon.get("/api/v1/auth/me", headers=headers).status_code == 200


def test_reativar_com_nome_ja_usado_por_outro_ativo_e_recusado(
    client: TestClient, db: Session, entrar_como
):
    alvo = _inativo_de_antes_da_migracao(db, "Nome Repetido")
    entrar_como("Nome Repetido")

    r = client.post(f"/api/v1/usuarios/{alvo.id}/reativar")
    assert r.status_code == 422
    assert "nome" in r.text

    db.refresh(alvo)
    assert alvo.ativo is False
    assert alvo.senha_provisoria is False


def test_reativar_registra_na_auditoria_sem_a_senha(client: TestClient, db: Session):
    alvo = _inativo_de_antes_da_migracao(db, "Reativado Auditado")
    senha = client.post(f"/api/v1/usuarios/{alvo.id}/reativar").json()["senha_gerada"]

    logs = client.get(
        "/api/v1/auditoria", params={"entidade": "usuario", "entidade_id": alvo.id}
    ).json()["items"]
    assert any(x["dados"] == {"reativado": True, "senha_alterada": True} for x in logs)
    assert senha not in str(logs)
