"""Verificação em duas etapas com código de 6 números (TOTP -- o mesmo do
Google Authenticator, Microsoft Authenticator, Authy...).

A pessoa escaneia um QR code uma vez; depois, no login, além da senha
digita o código que o aplicativo mostra (muda a cada 30 segundos). Assim,
uma senha vazada sozinha não basta pra entrar.
"""

import hmac
import time

import pyotp

EMISSOR = "Casa Espírita Amor e Perdão"
_INTERVALO = 30


def novo_segredo() -> str:
    return pyotp.random_base32()


def uri_de_configuracao(segredo: str, nome_usuario: str) -> str:
    """O conteúdo do QR code (otpauth://...)."""
    return pyotp.TOTP(segredo).provisioning_uri(name=nome_usuario, issuer_name=EMISSOR)


def _so_digitos(codigo: str) -> str:
    return "".join(c for c in codigo if c.isdigit())


def verificar(segredo: str, codigo: str, ultimo_passo: int | None) -> int | None:
    """Confere o código e devolve o "passo" (janela de 30s) em que ele bate.

    Aceita o passo anterior e o seguinte também (relógio do celular meio
    adiantado/atrasado). Recusa um passo já usado -- quem espiar um código
    não consegue reaproveitá-lo.
    """
    codigo = _so_digitos(codigo)
    if len(codigo) != 6:
        return None
    totp = pyotp.TOTP(segredo)
    agora = int(time.time()) // _INTERVALO
    for passo in (agora - 1, agora, agora + 1):
        if ultimo_passo is not None and passo <= ultimo_passo:
            continue
        if hmac.compare_digest(totp.at(passo * _INTERVALO), codigo):
            return passo
    return None
