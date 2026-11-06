"""Senha provisória: gerada pelo servidor, mostrada uma vez, válida por 72h.

Regressão do achado #1 de security-audit/NEEDS-VALIDATION.md: antes a tela
sugeria os 8 primeiros números do CPF como senha provisória, e ela nunca
vencia -- quem lesse o CPF da ficha da pessoa entrava na conta dela.

O "relógio" é simulado mudando senha_provisoria_expira_em direto no banco de
teste (a transação é desfeita no fim de cada teste).
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from tests.conftest import SENHA_BOA

CPF = "39053344705"
SENHA_DO_CPF = CPF[:8]


def _criar(client: TestClient, nome: str, papel: str = "operador") -> dict:
    r = client.post("/api/v1/usuarios", json={"nome": nome, "papel": papel})
    assert r.status_code == 201, r.text
    return r.json()


def _login(client_anon: TestClient, nome: str, senha: str, **extra):
    return client_anon.post(
        "/api/v1/auth/login", data={"username": nome, "password": senha, **extra}
    )


def _vencer(db: Session, usuario_id: int, *, ha: timedelta = timedelta(minutes=1)):
    """Faz de conta que o prazo da senha provisória já passou."""
    usuario = db.get(Usuario, usuario_id)
    usuario.senha_provisoria_expira_em = datetime.now(UTC) - ha
    db.flush()


# ---------- o servidor gera a senha ----------


def test_criar_usuario_devolve_senha_aleatoria_gerada_pelo_servidor(
    client: TestClient, client_anon: TestClient
):
    a = _criar(client, "Gerada Um")
    b = _criar(client, "Gerada Dois")

    assert len(a["senha_gerada"]) >= 16
    assert a["senha_gerada"] != b["senha_gerada"]
    assert not a["senha_gerada"].isdigit()

    r = _login(client_anon, "Gerada Um", a["senha_gerada"])
    assert r.status_code == 200, r.text
    assert r.json()["pendencias"] == ["trocar_senha"]


def test_senha_gerada_nao_aparece_em_outras_respostas(client: TestClient):
    criado = _criar(client, "Aparece Uma Vez")
    assert "senha_gerada" not in client.get(f"/api/v1/usuarios/{criado['id']}").json()
    lista = client.get("/api/v1/usuarios").json()["items"]
    assert all("senha_gerada" not in u for u in lista)


def test_admin_nao_escolhe_a_senha(client: TestClient):
    """Sem campo de senha, não tem como o admin usar o CPF (ou qualquer
    outra coisa adivinhável) como senha provisória."""
    r = client.post(
        "/api/v1/usuarios", json={"nome": "Quer Escolher", "senha": SENHA_DO_CPF}
    )
    assert r.status_code == 422

    criado = _criar(client, "Ja Existe")
    r = client.patch(f"/api/v1/usuarios/{criado['id']}", json={"senha": SENHA_DO_CPF})
    assert r.status_code == 422


def test_cpf_lido_da_ficha_nao_abre_conta_nova(
    client: TestClient, client_anon: TestClient, entrar_como
):
    """O encadeamento do relatório: o operador lê o CPF completo da ficha e
    tenta entrar na conta recém-criada (admin) com os 8 primeiros números."""
    pessoa = client.post(
        "/api/v1/pessoas",
        json={
            "nome_completo": "Maria Teste Silva",
            "cpf": CPF,
            "consentimento_lgpd": True,
        },
    )
    assert pessoa.status_code == 201, pessoa.text
    _criar(client, "Maria Silva", papel="admin")

    op = entrar_como("Operador Curioso")
    r = client_anon.get(f"/api/v1/pessoas/{pessoa.json()['id']}/cpf", headers=op)
    assert r.status_code == 200
    assert r.json()["cpf"] == CPF

    for chute in (SENHA_DO_CPF, CPF):
        r = _login(client_anon, "Maria Silva", chute)
        assert r.status_code == 401
        assert r.json()["detail"]["codigo"] == "credenciais"


# ---------- redefinir pelo admin ----------


def test_redefinir_gera_senha_nova_e_derruba_sessoes(
    client: TestClient, client_anon: TestClient, entrar_como
):
    headers = entrar_como("Joao Pereira")
    eu = client_anon.get("/api/v1/auth/me", headers=headers).json()

    r = client.post(f"/api/v1/usuarios/{eu['id']}/redefinir-senha")
    assert r.status_code == 200, r.text
    nova = r.json()["senha_gerada"]
    assert len(nova) >= 16
    assert r.json()["senha_provisoria"] is True

    # a sessão antiga caiu e a senha antiga não vale mais
    assert client_anon.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert _login(client_anon, "Joao Pereira", SENHA_BOA).status_code == 401

    login = _login(client_anon, "Joao Pereira", nova)
    assert login.status_code == 200
    assert login.json()["pendencias"] == ["trocar_senha"]

    # redefinir de novo invalida a senha gerada antes
    outra = client.post(f"/api/v1/usuarios/{eu['id']}/redefinir-senha").json()
    assert outra["senha_gerada"] != nova
    assert _login(client_anon, "Joao Pereira", nova).status_code == 401


def test_redefinir_nao_grava_a_senha_na_auditoria(client: TestClient, entrar_como):
    entrar_como("Auditado Aqui")
    alvo = next(
        u
        for u in client.get("/api/v1/usuarios").json()["items"]
        if u["nome"] == "Auditado Aqui"
    )
    senha = client.post(f"/api/v1/usuarios/{alvo['id']}/redefinir-senha").json()[
        "senha_gerada"
    ]
    logs = client.get(
        "/api/v1/auditoria", params={"entidade": "usuario", "entidade_id": alvo["id"]}
    ).json()["items"]
    assert any(x["dados"] == {"senha_alterada": True} for x in logs)
    assert senha not in str(logs)


def test_redefinir_quem_tem_mfa_continua_pedindo_o_codigo(
    client: TestClient, client_anon: TestClient, entrar_como
):
    """Controle que já existia e precisa continuar: redefinir só a senha não
    tira a verificação em duas etapas."""
    headers = entrar_como("Tem Mfa", papel="admin")
    eu = client_anon.get("/api/v1/auth/me", headers=headers).json()
    nova = client.post(f"/api/v1/usuarios/{eu['id']}/redefinir-senha").json()[
        "senha_gerada"
    ]
    r = _login(client_anon, "Tem Mfa", nova)
    assert r.status_code == 401
    assert r.json()["detail"]["codigo"] == "mfa_necessario"


# ---------- validade de 72h ----------


def test_senha_provisoria_vale_72_horas(client: TestClient):
    antes = datetime.now(UTC)
    criado = _criar(client, "Prazo Certo")
    expira = datetime.fromisoformat(criado["senha_expira_em"])
    esperado = antes + timedelta(hours=72)
    assert abs(expira - esperado) < timedelta(minutes=1)


def test_login_com_senha_provisoria_vencida_e_recusado(
    client: TestClient, client_anon: TestClient, db: Session
):
    criado = _criar(client, "Demorou Pra Entrar")

    # ainda no prazo (faltando 1 min): entra
    usuario = db.get(Usuario, criado["id"])
    usuario.senha_provisoria_expira_em = datetime.now(UTC) + timedelta(minutes=1)
    db.flush()
    r = _login(client_anon, "Demorou Pra Entrar", criado["senha_gerada"])
    assert r.status_code == 200

    # passou do prazo: recusado, com um aviso que a tela mostra
    _vencer(db, criado["id"])
    r = _login(client_anon, "Demorou Pra Entrar", criado["senha_gerada"])
    assert r.status_code == 401
    assert r.json()["detail"]["codigo"] == "senha_provisoria_vencida"

    # a recusa fica na auditoria, sem a senha
    logs = client.get(
        "/api/v1/auditoria", params={"entidade": "usuario", "entidade_id": criado["id"]}
    ).json()["items"]
    assert any(
        x["acao"] == "login_falha"
        and x["dados"] == {"motivo": "senha_provisoria_vencida"}
        for x in logs
    )


def test_senha_vencida_volta_a_valer_so_com_admin_redefinindo(
    client: TestClient, client_anon: TestClient, db: Session
):
    criado = _criar(client, "Pediu De Novo")
    _vencer(db, criado["id"], ha=timedelta(days=30))
    r = _login(client_anon, "Pediu De Novo", criado["senha_gerada"])
    assert r.status_code == 401

    nova = client.post(f"/api/v1/usuarios/{criado['id']}/redefinir-senha").json()
    assert _login(client_anon, "Pediu De Novo", nova["senha_gerada"]).status_code == 200


def test_sessao_aberta_com_senha_provisoria_cai_quando_ela_vence(
    client: TestClient, client_anon: TestClient, db: Session
):
    criado = _criar(client, "Entrou E Parou")
    token = _login(
        client_anon, "Entrou E Parou", criado["senha_gerada"], lembrar="true"
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client_anon.get("/api/v1/auth/me", headers=headers).status_code == 200

    _vencer(db, criado["id"])
    assert client_anon.get("/api/v1/auth/me", headers=headers).status_code == 401
    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": criado["senha_gerada"], "senha_nova": SENHA_BOA},
        headers=headers,
    )
    assert r.status_code == 401


def test_trocar_a_senha_tira_o_prazo(
    client: TestClient, client_anon: TestClient, db: Session
):
    criado = _criar(client, "Trocou Logo")
    token = _login(client_anon, "Trocou Logo", criado["senha_gerada"]).json()[
        "access_token"
    ]
    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": criado["senha_gerada"], "senha_nova": SENHA_BOA},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 204, r.text

    usuario = db.get(Usuario, criado["id"])
    assert usuario.senha_provisoria is False
    assert usuario.senha_provisoria_expira_em is None
    # a senha própria não vence
    assert _login(client_anon, "Trocou Logo", SENHA_BOA).status_code == 200
