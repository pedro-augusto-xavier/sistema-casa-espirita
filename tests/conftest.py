"""Configuração dos testes.

Cada teste roda dentro de uma transação que é desfeita no final (rollback),
então o banco volta ao estado anterior e um teste não interfere no outro.
Usa o mesmo banco do .env -- as tabelas já precisam existir (alembic upgrade head).
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import engine, get_db
from app.main import app


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
def client(db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
