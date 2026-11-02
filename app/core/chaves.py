"""Leitura das chaves de criptografia que vêm das variáveis de ambiente.

Fica separado de `cripto.py` (sem importar `settings`) pra própria
configuração conseguir validar o formato na hora em que o app sobe -- se a
chave estiver errada, é melhor o deploy falhar do que o app subir e quebrar
na primeira ficha aberta.

Formato de CHAVES_CRIPTOGRAFIA:  "id:chave_base64[,id:chave_base64...]"
  - cada chave tem 32 bytes (AES-256), em base64
  - a PRIMEIRA da lista é a ativa (usada pra cifrar o que é novo)
  - as outras só servem pra decifrar o que foi cifrado com elas antes
    (é assim que se troca de chave sem perder nada -- ver docs/SEGURANCA.md)
"""

import base64
import binascii
import hashlib

TAMANHO_CHAVE = 32


def _b64(texto: str) -> bytes:
    try:
        return base64.b64decode(texto.strip(), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("chave não está em base64 válido") from exc


def ler_chaves(bruto: str) -> tuple[int, dict[int, bytes]]:
    """Devolve (id da chave ativa, {id: chave})."""
    chaves: dict[int, bytes] = {}
    ativa: int | None = None
    for parte in bruto.split(","):
        parte = parte.strip()
        if not parte:
            continue
        id_txt, separador, chave_b64 = parte.partition(":")
        if not separador:
            raise ValueError("formato esperado: id:chave_base64 (ex: 1:AbC...=)")
        try:
            id_chave = int(id_txt)
        except ValueError as exc:
            raise ValueError("o id da chave precisa ser um número") from exc
        if not 1 <= id_chave <= 255:
            raise ValueError("o id da chave vai de 1 a 255")
        if id_chave in chaves:
            raise ValueError(f"id de chave repetido: {id_chave}")
        chave = _b64(chave_b64)
        if len(chave) != TAMANHO_CHAVE:
            raise ValueError("cada chave precisa ter 32 bytes (AES-256)")
        chaves[id_chave] = chave
        if ativa is None:
            ativa = id_chave
    if ativa is None:
        raise ValueError("nenhuma chave de criptografia configurada")
    return ativa, chaves


def ler_chave_hmac(bruto: str) -> bytes:
    chave = _b64(bruto)
    if len(chave) < TAMANHO_CHAVE:
        raise ValueError("a chave de HMAC precisa ter pelo menos 32 bytes")
    return chave


def _chave_dev(rotulo: str) -> str:
    return base64.b64encode(hashlib.sha256(rotulo.encode()).digest()).decode()


# Valores de desenvolvimento: deixam o projeto rodar logo depois do clone.
# A configuração recusa esses valores fora do dev (ver config.py).
CHAVES_DEV = "1:" + _chave_dev("casa-espirita/dev/criptografia")
CHAVE_HMAC_DEV = _chave_dev("casa-espirita/dev/hmac")
