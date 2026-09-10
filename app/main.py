"""Ponto de entrada da API.

Rodar em desenvolvimento:
    uvicorn app.main:app --reload

Documentação interativa (com a API rodando):
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.errors import ErroDominio, NaoEncontrado

app = FastAPI(
    title="Sistema Casa Espírita",
    description="Cadastro de pessoas, atendimentos e tratamentos.",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(ErroDominio)
def _erro_dominio(request: Request, exc: ErroDominio) -> JSONResponse:
    """Regra de negócio violada -> 404 se for referência inexistente, senão 422."""
    codigo = (
        status.HTTP_404_NOT_FOUND
        if isinstance(exc, NaoEncontrado)
        else status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    return JSONResponse(status_code=codigo, content={"detail": exc.mensagem})


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
