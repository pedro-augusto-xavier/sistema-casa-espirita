"""Conexão com o PostgreSQL usando SQLAlchemy 2.0.

- engine: o "motor" que abre conexões com o banco.
- SessionLocal: fábrica de sessões (cada requisição usa uma sessão).
- Base: classe-mãe de todos os modelos (tabelas).
- get_db: dependência do FastAPI que entrega uma sessão e fecha no fim.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # testa a conexão antes de usar (evita erro de conexão morta)
    echo=settings.is_dev,  # em dev, imprime o SQL gerado no console
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Todos os modelos herdam desta classe."""


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
