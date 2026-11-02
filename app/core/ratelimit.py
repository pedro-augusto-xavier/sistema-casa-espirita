"""Limite simples de tentativas por IP, em memória -- sem precisar de Redis.

Serve pra segurar login e troca de senha contra força bruta. Funciona bem
pro tamanho desse sistema (o Render roda uma instância só, então o estado
em memória não se perde entre requisições de um mesmo processo).

Importante: pra funcionar corretamente atrás do proxy do Render, o uvicorn
precisa rodar com `--proxy-headers` (ver DEPLOY.md) -- senão todo mundo
aparece com o mesmo IP e o limite vira um só pra equipe inteira.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

JANELA_SEGUNDOS = 5 * 60
LIMITE_TENTATIVAS = 10

# chave -> lista de timestamps (time.monotonic()) das tentativas na janela
_tentativas: dict[str, list[float]] = defaultdict(list)


def _ip_do_cliente(request: Request) -> str:
    return request.client.host if request.client else "desconhecido"


def limitar_tentativas(request: Request) -> None:
    """Dependência do FastAPI: barra com 429 quem exceder o limite.

    Usada nas rotas sensíveis (login, trocar senha) -- não em todo o site,
    só onde um ataque de força bruta faria sentido tentar.
    """
    agora = time.monotonic()
    chave = _ip_do_cliente(request)
    janela = _tentativas[chave]

    while janela and agora - janela[0] > JANELA_SEGUNDOS:
        janela.pop(0)

    if len(janela) >= LIMITE_TENTATIVAS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Espere alguns minutos e tente de novo.",
        )

    janela.append(agora)

    # evita a memória crescer pra sempre com IPs que só apareceram uma vez
    if len(_tentativas) > 10_000:
        _tentativas.clear()
