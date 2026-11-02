"""Cabeçalhos de resposta HTTP que reforçam a segurança do navegador --
coisas que não têm por que não estar lá, independente do resto."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class CabecalhosSeguranca(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        resposta = await call_next(request)
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["X-Frame-Options"] = "DENY"
        resposta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resposta.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        if not settings.is_dev:
            # só faz sentido quando o site já é servido em HTTPS (Render/Vercel)
            resposta.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains"
            )
        return resposta
