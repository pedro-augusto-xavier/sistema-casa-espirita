"""Schemas de Agenda (eventos) e Escala (quem trabalha em cada evento)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TipoEvento
from app.schemas.pessoa import PessoaMini


class EscalaIn(BaseModel):
    pessoa_id: int
    funcao: str | None = Field(default=None, max_length=80)


class EscalaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pessoa: PessoaMini
    funcao: str | None


class EventoAgendaCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    tipo: TipoEvento
    data_inicio: datetime
    data_fim: datetime | None = None
    recorrencia: str | None = Field(default=None, max_length=50)
    descricao: str | None = None
    escalados: list[EscalaIn] = Field(default_factory=list)


class EventoAgendaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    tipo: TipoEvento | None = None
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    recorrencia: str | None = None
    descricao: str | None = None
    ativo: bool | None = None
    escalados: list[EscalaIn] | None = None


class EventoAgendaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    tipo: TipoEvento
    data_inicio: datetime
    data_fim: datetime | None
    recorrencia: str | None
    descricao: str | None
    ativo: bool
    escalas: list[EscalaOut]


class EventoAgendaListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    tipo: TipoEvento
    data_inicio: datetime
    data_fim: datetime | None
    ativo: bool
    qtd_escalados: int
