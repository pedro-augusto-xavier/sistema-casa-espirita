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

    # login com e-mail + senha (form, não JSON)
    r = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "op@example.com", "password": "senha12345"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    eu = client_anon.get("/api/v1/auth/me", headers=headers)
    assert eu.status_code == 200
    assert eu.json()["email"] == "op@example.com"

    # com o token, consegue acessar rota protegida
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 200


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
        data={"username": "fulano@example.com", "password": "senhaerrada"},
    )
    assert r.status_code == 401


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
        data={"username": "op2@example.com", "password": "senha12345"},
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
