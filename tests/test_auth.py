"""Testes de autenticação e proteção de rotas."""

from fastapi.testclient import TestClient


def test_rota_protegida_sem_token_da_401(client_anon: TestClient):
    r = client_anon.get("/api/v1/pessoas")
    assert r.status_code == 401


def test_login_e_uso_do_token(client: TestClient, client_anon: TestClient):
    # admin cria um operador
    novo = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Operador Um",
            "email": "op@example.com",
            "senha": "senha12345",
            "papel": "operador",
        },
    )
    assert novo.status_code == 201, novo.text

    # login com nome + senha (form, não JSON) -- não é e-mail
    r = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "Operador Um", "password": "senha12345"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    eu = client_anon.get("/api/v1/auth/me", headers=headers)
    assert eu.status_code == 200
    assert eu.json()["nome"] == "Operador Um"

    # com o token, consegue acessar rota protegida
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 200


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


def test_senha_errada_da_401(client: TestClient, client_anon: TestClient):
    client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Fulano",
            "email": "fulano@example.com",
            "senha": "senhacerta1",
            "papel": "operador",
        },
    )
    r = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "Fulano", "password": "senhaerrada"},
    )
    assert r.status_code == 401


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


def test_operador_nao_acessa_gestao_de_usuarios(
    client: TestClient, client_anon: TestClient
):
    client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Operador Dois",
            "email": "op2@example.com",
            "senha": "senha12345",
            "papel": "operador",
        },
    )
    token = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "Operador Dois", "password": "senha12345"},
    ).json()["access_token"]

    r = client_anon.get(
        "/api/v1/usuarios", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 403


def test_token_invalido_da_401(client_anon: TestClient):
    r = client_anon.get(
        "/api/v1/pessoas", headers={"Authorization": "Bearer isso.nao.e.um.token"}
    )
    assert r.status_code == 401
