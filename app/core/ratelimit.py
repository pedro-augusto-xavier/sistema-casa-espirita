"""Limite de tentativas erradas, em memória -- sem precisar de Redis.

Segura login, troca de senha e códigos de verificação contra força bruta.
Conta só as FALHAS: quem acerta a senha não gasta tentativa.

Dois limites no login, como recomendado:
  - por IP: um IP que erra muito (tentando vários nomes) é barrado;
  - por conta: um nome que recebe muitas senhas erradas é barrado, mesmo
    que o atacante troque de IP a cada tentativa.

O Render roda uma instância só, então o estado em memória vale pra todas
as requisições. (Se um dia tiver mais de uma instância, isso precisa ir
pro banco ou pra um Redis.)
"""

import time
from collections import defaultdict

from fastapi import HTTPException, status

MENSAGEM_BLOQUEIO = "Muitas tentativas. Espere alguns minutos e tente de novo."


class LimiteDeFalhas:
    def __init__(self, limite: int, janela_segundos: int) -> None:
        self.limite = limite
        self.janela = janela_segundos
        self._falhas: dict[str, list[float]] = defaultdict(list)

    def _janela_de(self, chave: str) -> list[float]:
        agora = time.monotonic()
        janela = self._falhas[chave]
        while janela and agora - janela[0] > self.janela:
            janela.pop(0)
        return janela

    def bloqueado(self, chave: str) -> bool:
        return len(self._janela_de(chave)) >= self.limite

    def exigir_liberado(self, chave: str) -> None:
        if self.bloqueado(chave):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=MENSAGEM_BLOQUEIO,
                headers={"Retry-After": str(self.janela)},
            )

    def registrar_falha(self, chave: str) -> None:
        self._janela_de(chave).append(time.monotonic())
        # evita a memória crescer pra sempre com chaves que só apareceram 1x
        if len(self._falhas) > 10_000:
            self._falhas.clear()

    def limpar(self, chave: str) -> None:
        self._falhas.pop(chave, None)

    def zerar(self) -> None:
        self._falhas.clear()


# 10 erros em 5 min por IP; 5 erros em 5 min na mesma conta.
falhas_por_ip = LimiteDeFalhas(limite=10, janela_segundos=5 * 60)
falhas_por_conta = LimiteDeFalhas(limite=5, janela_segundos=5 * 60)


def chave_conta(nome: str) -> str:
    return "conta:" + " ".join(nome.split()).lower()


def chave_usuario(usuario_id: int) -> str:
    return f"usuario:{usuario_id}"


def chave_ip(ip: str | None) -> str:
    return f"ip:{ip or 'desconhecido'}"


def zerar_limites() -> None:
    """Usado pelos testes (o TestClient usa sempre o mesmo IP)."""
    falhas_por_ip.zerar()
    falhas_por_conta.zerar()
