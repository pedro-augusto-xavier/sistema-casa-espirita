"""Schemas de SessaoGrupo (Grupo Despertar, Grupo de Estudos) e presença."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pessoa import PessoaMini


class PresencaIn(BaseModel):
    pessoa_id: int


class PresencaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pessoa: PessoaMini


class SessaoGrupoCreate(BaseModel):
    tipo_tratamento_id: int
    data: date | None = None
    responsavel_id: int | None = None
    observacao: str | None = None
    presentes: list[PresencaIn] = Field(default_factory=list)


class SessaoGrupoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: date | None = None
    responsavel_id: int | None = None
    observacao: str | None = None
    presentes: list[PresencaIn] | None = None


class SessaoGrupoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_tratamento_id: int
    tipo_nome: str
    data: date
    responsavel: PessoaMini | None
    observacao: str | None
    presencas: list[PresencaOut]


class SessaoGrupoListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_nome: str
    data: date
    responsavel: PessoaMini | None
    qtd_presentes: int
