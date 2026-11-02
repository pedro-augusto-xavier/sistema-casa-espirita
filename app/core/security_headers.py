"""Cabeçalhos de resposta HTTP que reforçam a segurança do navegador --
coisas que não têm por que não estar lá, independente do resto."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

# A API só devolve JSON e arquivos: nada de script, frame ou estilo.
_CSP_API = "default-src 'none'; frame-ancestors 'none'"
_CAMINHOS_DA_DOCUMENTACAO = ("/docs", "/redoc")


class CabecalhosSeguranca(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        resposta = await call_next(request)
        cabecalhos = resposta.headers
        cabecalhos["X-Content-Type-Options"] = "nosniff"
        cabecalhos["X-Frame-Options"] = "DENY"
        cabecalhos["Referrer-Policy"] = "strict-origin-when-cross-origin"
        cabecalhos["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if not request.url.path.startswith(_CAMINHOS_DA_DOCUMENTACAO):
            # a rota de anexo manda uma CSP própria (mais restrita ainda)
            cabecalhos.setdefault("Content-Security-Policy", _CSP_API)
        if request.url.path.startswith("/api/"):
            # respostas com dado pessoal não ficam guardadas em cache do
            # navegador nem de proxy no caminho
            cabecalhos.setdefault("Cache-Control", "no-store")
        if not settings.is_dev:
            # só faz sentido quando o site já é servido em HTTPS (Render/Vercel)
            cabecalhos["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains"
            )
        return resposta
