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

from fastapi import HTTPException, status

MENSAGEM_BLOQUEIO = "Muitas tentativas. Espere alguns minutos e tente de novo."

# Passando disso, as chaves cujas falhas já venceram são removidas.
MAX_CHAVES = 10_000


class LimiteDeFalhas:
    def __init__(self, limite: int, janela_segundos: int) -> None:
        self.limite = limite
        self.janela = janela_segundos
        self._falhas: dict[str, list[float]] = {}

    def _recentes(self, chave: str) -> list[float]:
        """Falhas da chave ainda dentro da janela. Só consulta: não cria a
        chave (senão qualquer nome digitado ocuparia espaço)."""
        janela = self._falhas.get(chave)
        if not janela:
            return []
        agora = time.monotonic()
        while janela and agora - janela[0] > self.janela:
            janela.pop(0)
        if not janela:
            del self._falhas[chave]
        return janela

    def bloqueado(self, chave: str) -> bool:
        return len(self._recentes(chave)) >= self.limite

    def exigir_liberado(self, chave: str) -> None:
        if self.bloqueado(chave):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=MENSAGEM_BLOQUEIO,
                headers={"Retry-After": str(self.janela)},
            )

    def registrar_falha(self, chave: str) -> None:
        self._recentes(chave)  # descarta as falhas vencidas dessa chave
        agora = time.monotonic()
        self._falhas.setdefault(chave, []).append(agora)
        # evita a memória crescer pra sempre com chaves que só apareceram 1x.
        # Remove só as que já venceram: apagar tudo zeraria também quem está
        # bloqueado agora (dava pra destravar uma conta enchendo de nomes).
        if len(self._falhas) > MAX_CHAVES:
            self._remover_vencidas(agora)

    def _remover_vencidas(self, agora: float) -> None:
        vencidas = [
            chave
            for chave, janela in self._falhas.items()
            if agora - janela[-1] > self.janela
        ]
        for chave in vencidas:
            del self._falhas[chave]

    def limpar(self, chave: str) -> None:
        self._falhas.pop(chave, None)

    def zerar(self) -> None:
        self._falhas.clear()


# 10 erros em 5 min por IP; 5 erros em 5 min na mesma conta.
falhas_por_ip = LimiteDeFalhas(limite=10, janela_segundos=5 * 60)
falhas_por_conta = LimiteDeFalhas(limite=5, janela_segundos=5 * 60)

# Busca por CPF completo (GET /pessoas?q=) que não acha ninguém: 10 por hora
# por usuário. A ficha mostra 6 dos 11 dígitos e os 2 verificadores saem
# dos 9 primeiros, então sobram só 1.000 palpites -- sem limite, a busca
# viraria um jeito de descobrir o CPF inteiro sem passar pela auditoria.
# Instância própria: errar CPF não pode travar a troca de senha (que usa
# falhas_por_conta com a mesma chave_usuario).
buscas_cpf_sem_acerto = LimiteDeFalhas(limite=10, janela_segundos=60 * 60)


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
    buscas_cpf_sem_acerto.zerar()
