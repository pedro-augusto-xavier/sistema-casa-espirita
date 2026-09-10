"""Validações do domínio brasileiro."""

import re

_NAO_DIGITO = re.compile(r"\D")


def so_digitos(valor: str) -> str:
    return _NAO_DIGITO.sub("", valor or "")


def cpf_valido(cpf: str) -> bool:
    """Confere os dígitos verificadores do CPF."""
    cpf = so_digitos(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for tamanho in (9, 10):
        soma = sum(
            int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho)
        )
        digito = (soma * 10) % 11
        digito = 0 if digito == 10 else digito
        if digito != int(cpf[tamanho]):
            return False
    return True


def normaliza_cep(cep: str | None) -> str | None:
    """Deixa o CEP no formato 00000-000 (ou None se vazio/ inválido)."""
    if not cep:
        return None
    digitos = so_digitos(cep)
    if len(digitos) != 8:
        return None
    return f"{digitos[:5]}-{digitos[5:]}"
