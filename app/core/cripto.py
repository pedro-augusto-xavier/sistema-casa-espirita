"""Criptografia dos campos sensíveis (AES-256-GCM) e HMAC pra busca.

Por quê: se alguém conseguir uma cópia do banco (senha do Neon vazada, um
backup perdido...), CPF, observações e anexos aparecem só como bytes
embaralhados. A chave fica fora do banco e fora do Git -- numa variável de
ambiente do servidor (Render).

O que vai pro banco:
    [versão do formato = 1][id da chave][nonce, 12 bytes][texto cifrado + tag]

- O id da chave permite trocar de chave (rotação) sem perder o que foi
  cifrado com a anterior. `scripts/rotacionar_chaves.py` faz a troca.
- O "contexto" (ex: "pessoa.cpf") entra como dado associado (AAD): um valor
  cifrado não pode ser copiado de uma coluna pra outra e decifrado lá.
- AES-GCM também autentica: se alguém mexer nos bytes, a leitura falha em
  vez de devolver lixo.

Uso nos modelos: as colunas usam os tipos `TextoCifrado` / `BytesCifrados`
daqui de baixo, e o resto do código lê e grava texto normal. A única coisa
que NÃO funciona é comparar no SQL (`Pessoa.cpf == "..."`): cada gravação
gera bytes diferentes. Pra achar CPF existe a coluna `cpf_hash` (HMAC).
"""

import hashlib
import hmac
import os
from functools import lru_cache

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import LargeBinary
from sqlalchemy.types import TypeDecorator

from app.core.chaves import ler_chave_hmac, ler_chaves
from app.core.config import settings

VERSAO_FORMATO = 1
_TAMANHO_NONCE = 12
_CABECALHO = 2  # versão + id da chave


class ErroCriptografia(Exception):
    """Dado cifrado ilegível: chave errada/ausente ou bytes adulterados."""


@lru_cache
def _chaves() -> tuple[int, dict[int, bytes]]:
    return ler_chaves(settings.CHAVES_CRIPTOGRAFIA)


@lru_cache
def _chave_hmac() -> bytes:
    return ler_chave_hmac(settings.CHAVE_HMAC)


def recarregar_chaves() -> None:
    """Esquece as chaves em cache (usado nos testes e na rotação)."""
    _chaves.cache_clear()
    _chave_hmac.cache_clear()


def id_chave_ativa() -> int:
    return _chaves()[0]


def cifrar(dados: bytes, contexto: str) -> bytes:
    ativa, chaves = _chaves()
    nonce = os.urandom(_TAMANHO_NONCE)
    cifrado = AESGCM(chaves[ativa]).encrypt(nonce, dados, contexto.encode())
    return bytes([VERSAO_FORMATO, ativa]) + nonce + cifrado


def decifrar(blob: bytes, contexto: str) -> bytes:
    if len(blob) < _CABECALHO + _TAMANHO_NONCE + 16 or blob[0] != VERSAO_FORMATO:
        raise ErroCriptografia("formato de dado cifrado desconhecido")
    _, chaves = _chaves()
    chave = chaves.get(blob[1])
    if chave is None:
        raise ErroCriptografia(
            f"dado cifrado com a chave {blob[1]}, que não está configurada"
        )
    nonce = blob[_CABECALHO : _CABECALHO + _TAMANHO_NONCE]
    try:
        return AESGCM(chave).decrypt(
            nonce, blob[_CABECALHO + _TAMANHO_NONCE :], contexto.encode()
        )
    except InvalidTag as exc:
        raise ErroCriptografia("dado cifrado adulterado ou chave errada") from exc


def id_da_chave(blob: bytes) -> int:
    """Com qual chave este valor foi cifrado (pra saber o que falta rotacionar)."""
    return blob[1]


def hmac_busca(valor: str) -> str:
    """HMAC-SHA256 em hexadecimal -- dá pra comparar e indexar sem decifrar,
    mas sem a chave não dá pra testar CPFs um por um (como daria com um
    SHA-256 puro, já que só existem 10^11 CPFs possíveis)."""
    return hmac.new(_chave_hmac(), valor.encode(), hashlib.sha256).hexdigest()


class TextoCifrado(TypeDecorator):
    """Coluna de texto guardada cifrada (bytea no Postgres)."""

    impl = LargeBinary
    cache_ok = True

    def __init__(self, contexto: str) -> None:
        super().__init__()
        self.contexto = contexto

    def process_bind_param(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        return cifrar(value.encode("utf-8"), self.contexto)

    def process_result_value(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        return decifrar(bytes(value), self.contexto).decode("utf-8")


class BytesCifrados(TypeDecorator):
    """Coluna binária (ex: o arquivo de um anexo) guardada cifrada."""

    impl = LargeBinary
    cache_ok = True

    def __init__(self, contexto: str) -> None:
        super().__init__()
        self.contexto = contexto

    def process_bind_param(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        return cifrar(bytes(value), self.contexto)

    def process_result_value(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        return decifrar(bytes(value), self.contexto)
