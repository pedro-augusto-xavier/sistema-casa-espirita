"""Configuração dos testes.

Cada teste roda dentro de uma transação que é desfeita no final (rollback),
então o banco volta ao estado anterior e um teste não interfere no outro.
Usa o mesmo banco do .env -- as tabelas já precisam existir (alembic upgrade head).

- `_seed_referencias`: garante tipos de tratamento / funções uma vez por sessão.
- `client`: já autenticado como admin (a maioria dos testes é sobre o CRUD).
- `client_anon`: sem autenticação, para testar login e proteção de rota.
- `entrar_como`: cria um usuário pronto pra uso (sem pendência) e devolve o
  cabeçalho com o token dele -- pros testes de permissão.
"""

from collections.abc import Callable, Generator

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import engine, get_db
from app.core.ratelimit import zerar_limites
from app.core.security import hash_senha
from app.crud import sessao as crud_sessao
from app.main import app
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario
from scripts.seed import run as rodar_seed

SENHA_BOA = "pao-de-queijo-quentinho"


@pytest.fixture(scope="session", autouse=True)
def _seed_referencias() -> None:
    rodar_seed()


@pytest.fixture(autouse=True)
def _zera_limite_de_tentativas() -> None:
    """O TestClient usa sempre o mesmo IP fake -- sem isso, os logins de um
    teste contariam pro limite do próximo."""
    zerar_limites()


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
    """Admin já com a verificação em duas etapas configurada (é obrigatória
    pra admin) e senha definitiva -- ou seja, sem pendência nenhuma."""
    u = db.scalar(select(Usuario).where(Usuario.email == "admin@example.com"))
    if u is None:
        u = Usuario(
            nome="Admin de Teste",
            email="admin@example.com",
            senha_hash=hash_senha(SENHA_BOA),
            papel=PapelUsuario.admin,
            senha_provisoria=False,
            mfa_ativo=True,
            mfa_segredo=pyotp.random_base32(),
        )
        db.add(u)
        db.flush()
    return u


@pytest.fixture()
def client(db: Session, usuario_admin: Usuario) -> Generator[TestClient, None, None]:
    """Cliente autenticado como admin, com uma sessão de verdade."""
    app.dependency_overrides[get_db] = lambda: db
    token = crud_sessao.abrir(db, usuario_admin)
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def client_anon(db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def entrar_como(db: Session) -> Callable[..., dict[str, str]]:
    """entrar_como("Fulana", papel="operador") -> {"Authorization": ...}"""

    def _entrar(nome: str, *, papel: str = "operador") -> dict[str, str]:
        usuario = Usuario(
            nome=nome,
            senha_hash=hash_senha(SENHA_BOA),
            papel=PapelUsuario(papel),
            senha_provisoria=False,
            mfa_ativo=papel == "admin",
            mfa_segredo=pyotp.random_base32() if papel == "admin" else None,
        )
        db.add(usuario)
        db.flush()
        return {"Authorization": f"Bearer {crud_sessao.abrir(db, usuario)}"}

    return _entrar
