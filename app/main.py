"""Ponto de entrada da API.

Rodar em desenvolvimento:
    uvicorn app.main:app --reload

Documentação interativa (só em desenvolvimento -- em produção fica
desligada, pra não entregar o mapa da API pra quem não deve):
    http://127.0.0.1:8000/docs
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api.deps import SessaoDB
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.contexto import ContextoDaRequisicao
from app.core.cripto import chaves_abrem_os_dados
from app.core.errors import Conflito, ErroDominio, NaoEncontrado
from app.core.security_headers import CabecalhosSeguranca

logger = logging.getLogger("app")


class _SemQueryStringNoLog(logging.Filter):
    """O log de acesso do uvicorn imprime a URL inteira -- e a busca de
    pessoas vai na URL (?q=...), que pode ser um CPF ou um nome. Corta tudo
    depois do "?" antes de ir pro log do Render."""

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple) and len(args) >= 3 and isinstance(args[2], str):
            record.args = (*args[:2], args[2].split("?", 1)[0], *args[3:])
        return True


logging.getLogger("uvicorn.access").addFilter(_SemQueryStringNoLog())

app = FastAPI(
    title="Sistema Casa Espírita",
    description="Cadastro de pessoas, atendimentos e tratamentos.",
    version="1.0.0",
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
    openapi_url="/openapi.json" if settings.is_dev else None,
)

app.add_middleware(CabecalhosSeguranca)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,  # o token vai no cabeçalho, não em cookie
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# por último = o mais de fora: o IP fica disponível pra tudo que vem depois
app.add_middleware(ContextoDaRequisicao)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(ErroDominio)
def _erro_dominio(request: Request, exc: ErroDominio) -> JSONResponse:
    """Regra de negócio violada -> 404 se for referência inexistente, 409 se
    esbarra no estado do registro, senão 422."""
    if isinstance(exc, NaoEncontrado):
        codigo = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, Conflito):
        codigo = status.HTTP_409_CONFLICT
    else:
        codigo = status.HTTP_422_UNPROCESSABLE_CONTENT
    return JSONResponse(status_code=codigo, content={"detail": exc.mensagem})


@app.exception_handler(RequestValidationError)
def _erro_de_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Igual ao padrão do FastAPI, mas SEM devolver o valor que foi enviado
    (`input`) -- numa troca de senha recusada, por exemplo, a senha voltaria
    na resposta e poderia parar em log de proxy ou do navegador."""
    erros = [
        {"loc": list(e.get("loc", ())), "msg": e.get("msg"), "type": e.get("type")}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": erros}
    )


@app.exception_handler(IntegrityError)
def _erro_de_integridade(request: Request, exc: IntegrityError) -> JSONResponse:
    """Violação de regra do banco (ex: duplicado que escapou da checagem).
    O detalhe (com o SQL) vai só pro log do servidor, nunca pra resposta."""
    logger.warning(
        "IntegrityError em %s %s: %s", request.method, request.url.path, exc.orig
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Conflito com um registro que já existe."},
    )


@app.exception_handler(Exception)
def _erro_inesperado(request: Request, exc: Exception) -> JSONResponse:
    """Qualquer outro erro: mensagem genérica pra quem chamou, detalhe
    completo (stack trace) só no log do servidor."""
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": (
                "Erro interno. Tente de novo; se continuar, avise quem cuida "
                "do sistema."
            )
        },
    )


@app.get("/", tags=["status"])
def raiz() -> dict:
    return {"app": "Sistema Casa Espírita"}


@app.get("/health", tags=["status"])
def health(db: SessaoDB) -> JSONResponse:
    """Confere se a API está de pé, se o banco responde e se as chaves de
    criptografia configuradas abrem os dados que estão no banco.

    Responde 503 se algo falhar. O Render chama esta rota antes de pôr uma
    versão nova no ar: com uma chave errada no painel, o deploy é barrado e
    a versão que funciona continua atendendo.
    """
    try:
        db.execute(text("SELECT 1"))
        banco_ok = True
    except Exception:
        banco_ok = False

    cripto_ok = banco_ok and chaves_abrem_os_dados(db)
    tudo_ok = banco_ok and cripto_ok
    codigo = status.HTTP_200_OK if tudo_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=codigo,
        content={
            "api": "ok",
            "banco": "ok" if banco_ok else "sem conexão",
            "cripto": "ok" if cripto_ok else "erro",
        },
    )
