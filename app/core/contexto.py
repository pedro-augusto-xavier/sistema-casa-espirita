"""Quem está fazendo a requisição (IP e navegador), disponível em qualquer
lugar do código sem precisar passar o `Request` de mão em mão -- a
auditoria e as sessões usam isso.

Sobre o IP: segundo a documentação do Render, toda requisição para um web
service passa pela Cloudflare e depois pelo balanceador do Render. A
Cloudflare manda o IP de quem conectou nela no cabeçalho `CF-Connecting-IP`
(um IP só) e recomenda ler esse cabeçalho em vez do `X-Forwarded-For`: neste
último ela só ACRESCENTA no fim da lista o que o cliente mandou, e a posição
do IP real depende de o balanceador do Render acrescentar mais um item ou
não -- coisa que o Render não documenta.

O nome do cabeçalho vem de IP_CLIENTE_CABECALHO (padrão `cf-connecting-ip`).
Vazio = não tem proxy na frente e vale o IP da conexão.

Quando o cabeçalho esperado não chega (ou não é um IP), o IP gravado na
auditoria e na sessão vem da conexão, mas ele NÃO é confiável: atrás do
Render ele é o primeiro item do X-Forwarded-For (o cliente escreve) ou o IP
do balanceador (o mesmo pra todo mundo). Por isso `ip_confiavel()` fica
falso e o login não aplica o limite por IP -- o limite por conta continua.
Melhor perder o limite por IP do que travar o login de todo mundo.
"""

import ipaddress
import logging
from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings

logger = logging.getLogger(__name__)

_ip: ContextVar[str | None] = ContextVar("ip_da_requisicao", default=None)
_ip_confiavel: ContextVar[bool] = ContextVar("ip_confiavel", default=False)
_user_agent: ContextVar[str | None] = ContextVar("user_agent", default=None)

_avisou_sem_cabecalho = False


def ip_atual() -> str | None:
    return _ip.get()


def ip_confiavel() -> bool:
    """True se o IP veio da fonte configurada (o cabeçalho do proxy, ou a
    conexão quando não tem proxy). Só aí dá pra limitar tentativas por IP."""
    return _ip_confiavel.get()


def user_agent_atual() -> str | None:
    return _user_agent.get()


def _ip_valido(texto: str) -> str | None:
    try:
        return str(ipaddress.ip_address(texto.strip()))
    except ValueError:
        return None


def _ip_do_escopo(scope: Scope, cabecalho: bytes) -> tuple[str, bool]:
    """Devolve (ip, confiavel)."""
    cliente = scope.get("client")
    ip_da_conexao = (cliente[0] if cliente else "desconhecido")[:64]
    if not cabecalho:
        return ip_da_conexao, True

    for nome, valor in scope.get("headers") or []:
        if nome == cabecalho:
            ip = _ip_valido(valor.decode("latin1"))
            if ip:
                return ip, True
            break

    # o health check do Render bate direto no app, sem passar pela
    # Cloudflare: não tem o cabeçalho e não deve gastar o aviso único
    global _avisou_sem_cabecalho
    if not _avisou_sem_cabecalho and scope.get("path") != "/health":
        _avisou_sem_cabecalho = True
        logger.warning(
            "Requisição sem um IP válido no cabeçalho %s: o limite de "
            "tentativas por IP fica desligado nesses casos (o por conta "
            "continua). Se o app está atrás de outro proxy, ajuste "
            "IP_CLIENTE_CABECALHO. (Aviso só uma vez.)",
            cabecalho.decode("latin1"),
        )
    return ip_da_conexao, False


class ContextoDaRequisicao:
    """Middleware ASGI puro (não BaseHTTPMiddleware) pra o contextvar
    chegar certinho até as rotas síncronas, que rodam em outra thread."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.cabecalho_ip = (
            settings.IP_CLIENTE_CABECALHO.strip().lower().encode("latin1")
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        user_agent = ""
        for nome, valor in scope.get("headers") or []:
            if nome == b"user-agent":
                user_agent = valor.decode("latin1")[:255]
                break

        ip, confiavel = _ip_do_escopo(scope, self.cabecalho_ip)
        token_ip = _ip.set(ip)
        token_confiavel = _ip_confiavel.set(confiavel)
        token_ua = _user_agent.set(user_agent or None)
        try:
            await self.app(scope, receive, send)
        finally:
            _ip.reset(token_ip)
            _ip_confiavel.reset(token_confiavel)
            _user_agent.reset(token_ua)
