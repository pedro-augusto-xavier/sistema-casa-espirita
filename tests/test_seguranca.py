"""Testes das proteções de segurança: limite de tentativas, trocar senha
e a trava contra SECRET_KEY fraca em produção."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.ratelimit import LIMITE_TENTATIVAS


def test_login_e_bloqueado_apos_muitas_tentativas(client_anon: TestClient):
    for _ in range(LIMITE_TENTATIVAS):
        r = client_anon.post(
            "/api/v1/auth/login",
            data={"username": "ninguem", "password": "errada"},
        )
        assert r.status_code == 401

    bloqueado = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "ninguem", "password": "errada"},
    )
    assert bloqueado.status_code == 429


def test_trocar_a_propria_senha(client: TestClient, client_anon: TestClient):
    client.post(
        "/api/v1/usuarios",
        json={"nome": "Troca Senha", "senha": "senhaantiga1", "papel": "operador"},
    )
    token = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "Troca Senha", "password": "senhaantiga1"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": "senhaantiga1", "senha_nova": "senhanovaboa1"},
        headers=headers,
    )
    assert r.status_code == 204, r.text

    # a senha antiga não funciona mais
    velha = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "Troca Senha", "password": "senhaantiga1"},
    )
    assert velha.status_code == 401

    # a nova funciona
    nova = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "Troca Senha", "password": "senhanovaboa1"},
    )
    assert nova.status_code == 200


def test_trocar_senha_com_senha_atual_errada_da_401(
    client: TestClient, client_anon: TestClient
):
    client.post(
        "/api/v1/usuarios",
        json={"nome": "Senha Errada Aqui", "senha": "senhacerta1", "papel": "operador"},
    )
    token = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "Senha Errada Aqui", "password": "senhacerta1"},
    ).json()["access_token"]

    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": "chutada", "senha_nova": "outrasenhaboa1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 401


def test_trocar_senha_exige_token(client_anon: TestClient):
    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": "x", "senha_nova": "umasenhaboa1"},
    )
    assert r.status_code == 401


def test_settings_recusa_chave_padrao_fora_do_dev():
    from app.core.config import Settings

    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            DATABASE_URL="postgresql+psycopg://u:p@localhost/db",
            SECRET_KEY="dev-inseguro-troque-no-.env",
            APP_ENV="production",
        )


def test_settings_recusa_chave_curta_fora_do_dev():
    from app.core.config import Settings

    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            DATABASE_URL="postgresql+psycopg://u:p@localhost/db",
            SECRET_KEY="curta",
            APP_ENV="production",
        )


def test_settings_aceita_chave_fraca_em_dev():
    """Em dev, a chave de exemplo passa -- não pode travar quem tá clonando
    o repo e rodando local pela primeira vez."""
    from app.core.config import Settings

    s = Settings(
        DATABASE_URL="postgresql+psycopg://u:p@localhost/db",
        SECRET_KEY="dev-inseguro-troque-no-.env",
        APP_ENV="dev",
    )
    assert s.SECRET_KEY == "dev-inseguro-troque-no-.env"


def test_resposta_tem_cabecalhos_de_seguranca(client_anon: TestClient):
    r = client_anon.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "referrer-policy" in r.headers
