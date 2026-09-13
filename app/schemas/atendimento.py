"""Schemas de Atendimento (a visita avulsa) e dos tratamentos aplicados nela."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Modalidade, TipoVinculo
from app.schemas.pessoa import PessoaMini, PessoaOut

# ---------- tratamentos dentro do atendimento ----------


class AssistidoRefIn(BaseModel):
    """Uma pessoa por quem o responsável pediu o tratamento, e o que ela é
    dele (filho, amigo...). Usado só pros tipos de formato "caso"."""

    pessoa_id: int
    vinculo_com_responsavel: TipoVinculo | None = None


class AtendimentoTratamentoIn(BaseModel):
    tipo_tratamento_id: int
    modalidade: Modalidade | None = None
    sessoes_previstas: int | None = Field(default=None, ge=0)
    sessoes_realizadas: int = Field(default=0, ge=0)
    observacao: str | None = None
    # só pros tipos de formato "caso" (Desobsessão): por quem a pessoa
    # pediu o tratamento (filhos, amigos, ela mesma). Vazio = ela mesma.
    assistidos: list[AssistidoRefIn] = Field(default_factory=list)


class AtendimentoTratamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_tratamento_id: int
    tipo_tratamento_nome: str
    modalidade: Modalidade | None
    sessoes_previstas: int | None
    sessoes_realizadas: int
    observacao: str | None


# ---------- atendimento ----------


class AtendimentoBase(BaseModel):
    pessoa_id: int
    data: date | None = None
    atendido_por_id: int | None = None
    solicitante_id: int | None = None
    presente: bool = True
    modalidade: Modalidade = Modalidade.presencial
    ordem_chegada: int | None = Field(default=None, ge=0)
    observacao: str | None = None
    retorno_previsto: date | None = None


class AtendimentoCreate(AtendimentoBase):
    tratamentos: list[AtendimentoTratamentoIn] = Field(default_factory=list)


class AtendimentoUpdate(BaseModel):
    """PATCH -- só chega o que muda. Se `tratamentos` vier, substitui a lista toda."""

    model_config = ConfigDict(extra="forbid")

    data: date | None = None
    atendido_por_id: int | None = None
    solicitante_id: int | None = None
    presente: bool | None = None
    modalidade: Modalidade | None = None
    ordem_chegada: int | None = Field(default=None, ge=0)
    observacao: str | None = None
    retorno_previsto: date | None = None
    tratamentos: list[AtendimentoTratamentoIn] | None = None


class AtendimentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data: date
    # dados completos da pessoa (nascimento, endereço, telefone) -- o PDF
    # da visita precisa deles, igual à ficha de papel.
    pessoa: PessoaOut
    atendido_por: PessoaMini | None
    solicitante: PessoaMini | None
    presente: bool
    modalidade: Modalidade
    ordem_chegada: int | None
    observacao: str | None
    retorno_previsto: date | None
    criado_em: datetime
    tratamentos: list[AtendimentoTratamentoOut]


class AtendimentoListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data: date
    pessoa: PessoaMini
    atendido_por: PessoaMini | None
    modalidade: Modalidade
    tratamentos_resumo: list[str]
