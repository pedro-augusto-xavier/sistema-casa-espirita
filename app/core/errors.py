"""Erros de regra de negócio.

A camada crud levanta ErroDominio quando algo é inválido (ex: tipo de
tratamento inexistente). O main.py transforma isso num HTTP 422 com a mensagem.
"""


class ErroDominio(Exception):
    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


class NaoEncontrado(ErroDominio):
    """Recurso referenciado não existe."""
