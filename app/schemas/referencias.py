"""Schemas das listas de referência (tipos de tratamento, funções)."""

from pydantic import BaseModel, ConfigDict

from app.models.enums import FormatoTratamento


class TipoTratamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    formato: FormatoTratamento
    ativo: bool


class FuncaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    ativo: bool
