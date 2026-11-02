"""Testes de autenticação, sessões e proteção de rotas."""

from fastapi.testclient import TestClient

from tests.conftest import SENHA_BOA


def _criar_e_logar(
    client: TestClient,
    client_anon: TestClient,
    nome: str,
    senha: str = "senha12345",
    papel: str = "operador",
) -> dict:
    """Admin cria o usuário (senha provisória) e a pessoa faz login."""
    r = client.post(
        "/api/v1/usuarios", json={"nome": nome, "senha": senha, "papel": papel}
    )
    assert r.status_code == 201, r.text
    r = client_anon.post(
        "/api/v1/auth/login", data={"username": nome, "password": senha}
    )
    assert r.status_code == 200, r.text
    return r.json()


def _cabecalho(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_rota_protegida_sem_token_da_401(client_anon: TestClient):
    r = client_anon.get("/api/v1/pessoas")
    assert r.status_code == 401


def test_primeiro_acesso_exige_trocar_a_senha_provisoria(
    client: TestClient, client_anon: TestClient
):
    login = _criar_e_logar(client, client_anon, "Operador Um")
    assert login["pendencias"] == ["trocar_senha"]
    headers = _cabecalho(login["access_token"])

    eu = client_anon.get("/api/v1/auth/me", headers=headers)
    assert eu.status_code == 200
    assert eu.json()["nome"] == "Operador Um"
    assert eu.json()["senha_provisoria"] is True

    # com a senha provisória, os dados ficam bloqueados
    bloqueado = client_anon.get("/api/v1/pessoas", headers=headers)
    assert bloqueado.status_code == 403
    assert bloqueado.json()["detail"]["codigo"] == "pendencia"

    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": "senha12345", "senha_nova": SENHA_BOA},
        headers=headers,
    )
    assert r.status_code == 204, r.text

    # a mesma sessão já fica liberada
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 200
    assert (
        client_anon.get("/api/v1/auth/me", headers=headers).json()["pendencias"] == []
    )


def test_login_ignora_maiuscula_e_espaco_nas_pontas(
    client: TestClient, client_anon: TestClient
):
    client.post(
        "/api/v1/usuarios",
        json={"nome": "Dona Marta", "senha": "senha12345", "papel": "operador"},
    )
    r = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "  dona marta  ", "password": "senha12345"},
    )
    assert r.status_code == 200, r.text


def test_email_e_opcional_no_cadastro_de_usuario(client: TestClient):
    r = client.post(
        "/api/v1/usuarios",
        json={"nome": "Sem Email", "senha": "senha12345", "papel": "operador"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["email"] is None
    assert r.json()["senha_provisoria"] is True


def test_senha_errada_e_usuario_inexistente_dao_a_mesma_resposta(
    client: TestClient, client_anon: TestClient
):
    client.post(
        "/api/v1/usuarios",
        json={"nome": "Fulano", "senha": "senhacerta1", "papel": "operador"},
    )
    senha_errada = client_anon.post(
        "/api/v1/auth/login", data={"username": "Fulano", "password": "senhaerrada"}
    )
    nao_existe = client_anon.post(
        "/api/v1/auth/login", data={"username": "Ninguem Aqui", "password": "x"}
    )
    assert senha_errada.status_code == nao_existe.status_code == 401
    assert senha_errada.json() == nao_existe.json()


def test_nome_duplicado_entre_ativos_da_erro(client: TestClient):
    client.post(
        "/api/v1/usuarios",
        json={"nome": "Nome Repetido", "senha": "senha12345", "papel": "operador"},
    )
    r = client.post(
        "/api/v1/usuarios",
        json={"nome": "nome repetido", "senha": "outrasenha1", "papel": "operador"},
    )
    assert r.status_code == 422


def test_nome_de_usuario_desativado_pode_ser_reusado(client: TestClient):
    primeiro = client.post(
        "/api/v1/usuarios",
        json={"nome": "Vai Sair", "senha": "senha12345", "papel": "operador"},
    ).json()
    client.patch(f"/api/v1/usuarios/{primeiro['id']}", json={"ativo": False})

    r = client.post(
        "/api/v1/usuarios",
        json={"nome": "Vai Sair", "senha": "outrasenha1", "papel": "operador"},
    )
    assert r.status_code == 201, r.text


def test_operador_nao_acessa_gestao_de_usuarios(client_anon: TestClient, entrar_como):
    headers = entrar_como("Operador Dois")
    # liberado pros dados...
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 200
    # ...mas não pra gestão de usuários
    r = client_anon.get("/api/v1/usuarios", headers=headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "Ação restrita a administradores"


def test_token_invalido_da_401(client_anon: TestClient):
    r = client_anon.get(
        "/api/v1/pessoas", headers={"Authorization": "Bearer isso.nao.e.um.token"}
    )
    assert r.status_code == 401


def test_manter_conectado_gera_token_mais_longo(
    client: TestClient, client_anon: TestClient
):
    from app.core.security import ler_token_acesso

    client.post(
        "/api/v1/usuarios",
        json={"nome": "Lembrada", "senha": "senha12345", "papel": "operador"},
    )

    def duracao(dados: dict) -> int:
        r = client_anon.post("/api/v1/auth/login", data=dados)
        assert r.status_code == 200, r.text
        payload = ler_token_acesso(r.json()["access_token"])
        return payload["exp"] - payload["iat"]

    base = {"username": "Lembrada", "password": "senha12345"}
    curto = duracao(base)
    longo = duracao({**base, "lembrar": "true"})
    assert longo > curto
    assert longo >= 29 * 24 * 3600


# ---------- sessões: cortar o acesso na hora ----------


def test_sair_invalida_o_token_no_servidor(client_anon: TestClient, entrar_como):
    headers = entrar_como("Vai Sair Agora")
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 200

    assert client_anon.post("/api/v1/auth/logout", headers=headers).status_code == 204
    # o mesmo token (ainda dentro da validade) não vale mais
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 401


def test_desativar_usuario_derruba_a_sessao_dele_na_hora(
    client: TestClient, client_anon: TestClient, entrar_como
):
    headers = entrar_como("Saiu Da Equipe")
    eu = client_anon.get("/api/v1/auth/me", headers=headers).json()
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 200

    client.patch(f"/api/v1/usuarios/{eu['id']}", json={"ativo": False})
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 401


def test_trocar_senha_derruba_as_outras_sessoes(
    client: TestClient, client_anon: TestClient
):
    login = _criar_e_logar(client, client_anon, "Duas Abas")
    aba1 = _cabecalho(login["access_token"])
    aba2 = _cabecalho(
        client_anon.post(
            "/api/v1/auth/login",
            data={"username": "Duas Abas", "password": "senha12345"},
        ).json()["access_token"]
    )
    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": "senha12345", "senha_nova": SENHA_BOA},
        headers=aba1,
    )
    assert r.status_code == 204
    assert client_anon.get("/api/v1/auth/me", headers=aba1).status_code == 200
    assert client_anon.get("/api/v1/auth/me", headers=aba2).status_code == 401


def test_admin_redefinir_senha_deixa_provisoria_e_derruba_sessao(
    client: TestClient, client_anon: TestClient, entrar_como
):
    headers = entrar_como("Esqueceu A Senha")
    eu = client_anon.get("/api/v1/auth/me", headers=headers).json()

    r = client.patch(f"/api/v1/usuarios/{eu['id']}", json={"senha": "39053344"})
    assert r.status_code == 200
    assert r.json()["senha_provisoria"] is True
    assert client_anon.get("/api/v1/auth/me", headers=headers).status_code == 401

    novo = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "Esqueceu A Senha", "password": "39053344"},
    ).json()
    assert novo["pendencias"] == ["trocar_senha"]


def test_admin_nao_desativa_nem_rebaixa_a_si_mesmo(client: TestClient, usuario_admin):
    r = client.patch(f"/api/v1/usuarios/{usuario_admin.id}", json={"ativo": False})
    assert r.status_code == 422
    r = client.patch(f"/api/v1/usuarios/{usuario_admin.id}", json={"papel": "operador"})
    assert r.status_code == 422
