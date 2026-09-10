"""Configuração dos testes.

Cada teste roda dentro de uma transação que é desfeita no final (rollback),
então o banco volta ao estado anterior e um teste não interfere no outro.
Usa o mesmo banco do .env -- as tabelas já precisam existir (alembic upgrade head).

- `_seed_referencias`: garante tipos de tratamento / funções uma vez por sessão.
- `client`: já autenticado como admin (a maioria dos testes é sobre o CRUD).
- `client_anon`: sem autenticação, para testar login e proteção de rota.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import engine, get_db
from app.core.security import criar_token_acesso, hash_senha
from app.main import app
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario
from scripts.seed import run as rodar_seed


@pytest.fixture(scope="session", autouse=True)
def _seed_referencias() -> None:
    rodar_seed()


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    conn = engine.connect()
    trans = conn.begin()
    sessao = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield sessao
    finally:
        sessao.close()
        trans.rollback()
        conn.close()


@pytest.fixture()
def usuario_admin(db: Session) -> Usuario:
    u = db.scalar(select(Usuario).where(Usuario.email == "admin@example.com"))
    if u is None:
        u = Usuario(
            nome="Admin de Teste",
            email="admin@example.com",
            senha_hash=hash_senha("senha-de-teste"),
            papel=PapelUsuario.admin,
        )
        db.add(u)
        db.flush()
    return u


@pytest.fixture()
def client(db: Session, usuario_admin: Usuario) -> Generator[TestClient, None, None]:
    """Cliente autenticado como admin, com um token JWT de verdade."""
    app.dependency_overrides[get_db] = lambda: db
    token = criar_token_acesso(usuario_admin.id, usuario_admin.papel.value)
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def client_anon(db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
