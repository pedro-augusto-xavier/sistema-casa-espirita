"""Ponto de entrada da API.

Rodar em desenvolvimento:
    uvicorn app.main:app --reload

Documentação interativa (com a API rodando):
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

app = FastAPI(
    title="Sistema Casa Espírita",
    description="Cadastro de pessoas, atendimentos e tratamentos.",
    version="0.1.0",
)


@app.get("/", tags=["status"])
def raiz() -> dict:
    return {"app": "Sistema Casa Espírita", "ambiente": settings.APP_ENV}


@app.get("/health", tags=["status"])
def health() -> dict:
    """Confere se a API está de pé e se o banco responde."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        banco_ok = True
    except Exception:
        banco_ok = False

    return {"api": "ok", "banco": "ok" if banco_ok else "sem conexão"}
