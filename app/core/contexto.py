"""Quem está fazendo a requisição (IP e navegador), disponível em qualquer
lugar do código sem precisar passar o `Request` de mão em mão -- a
auditoria e as sessões usam isso.

Sobre o IP: o Render fica atrás da Cloudflare, que manda o IP real do
cliente no cabeçalho `CF-Connecting-IP` e SOBRESCREVE qualquer valor que o
cliente tenha mandado nele. Já o `X-Forwarded-For` aceita o que o cliente
escrever no começo da lista -- não serve pra limitar tentativas de login.
Se um dia o servidor sair de trás da Cloudflare, ajuste CABECALHO_IP_REAL
aqui embaixo -- senão o cabeçalho pode ser forjado.
"""

from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send

CABECALHO_IP_REAL = b"cf-connecting-ip"

_ip: ContextVar[str | None] = ContextVar("ip_da_requisicao", default=None)
_user_agent: ContextVar[str | None] = ContextVar("user_agent", default=None)


def ip_atual() -> str | None:
    return _ip.get()


def user_agent_atual() -> str | None:
    return _user_agent.get()


def _ip_do_escopo(scope: Scope) -> str:
    for nome, valor in scope.get("headers") or []:
        if nome == CABECALHO_IP_REAL:
            ip = valor.decode("latin1").strip()
            if ip:
                return ip[:64]
    cliente = scope.get("client")
    return (cliente[0] if cliente else "desconhecido")[:64]


class ContextoDaRequisicao:
    """Middleware ASGI puro (não BaseHTTPMiddleware) pra o contextvar
    chegar certinho até as rotas síncronas, que rodam em outra thread."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        user_agent = ""
        for nome, valor in scope.get("headers") or []:
            if nome == b"user-agent":
                user_agent = valor.decode("latin1")[:255]
                break

        token_ip = _ip.set(_ip_do_escopo(scope))
        token_ua = _user_agent.set(user_agent or None)
        try:
            await self.app(scope, receive, send)
        finally:
            _ip.reset(token_ip)
            _user_agent.reset(token_ua)
