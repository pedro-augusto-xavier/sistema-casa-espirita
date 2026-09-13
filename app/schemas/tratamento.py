"""Schemas do Tratamento (caso de acompanhamento longo, tipo Desobsessão).

- Tratamento: aberto por um solicitante/responsável, com 1+ assistidos.
- TratamentoAssistido: cada pessoa do caso (conclui na sua hora).
- TratamentoEvolucao: o diário datado que os trabalhadores preenchem.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusAssistido, StatusTratamento, TipoVinculo
from app.schemas.pessoa import PessoaMini, PessoaOut

# ---------- assistidos ----------


class AssistidoIn(BaseModel):
    pessoa_id: int
    # o quê essa pessoa é do responsável do caso (filho, amigo...). Ignorado
    # quando pessoa_id é o próprio responsável.
    vinculo_com_responsavel: TipoVinculo | None = None


class AssistidoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: StatusAssistido | None = None
    situacao_final: str | None = None
    data_conclusao: date | None = None
    vinculo_com_responsavel: TipoVinculo | None = None


class AssistidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # dados completos (não só nome): a ficha em PDF do caso precisa de
    # nascimento, endereço e telefone, iguais aos da folha de papel.
    pessoa: PessoaOut
    status: StatusAssistido
    situacao_final: str | None
    data_conclusao: date | None
    vinculo_com_responsavel: TipoVinculo | None


# ---------- evolução (diário) ----------


class EvolucaoIn(BaseModel):
    texto: str = Field(min_length=1)
    data: date | None = None
    registrado_por_id: int | None = None
    pessoa_id: int | None = None


class EvolucaoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str | None = Field(default=None, min_length=1)
    data: date | None = None
    registrado_por_id: int | None = None
    pessoa_id: int | None = None


class EvolucaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data: date
    texto: str
    registrado_por: PessoaMini | None
    pessoa: PessoaMini | None
    criado_em: datetime


# ---------- tratamento (caso) ----------


class TratamentoCreate(BaseModel):
    tipo_tratamento_id: int
    solicitante_id: int | None = None
    data_inicio: date | None = None
    sessoes_previstas: int | None = Field(default=None, ge=0)
    observacao: str | None = None
    assistidos: list[AssistidoIn] = Field(default_factory=list)


class TratamentoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solicitante_id: int | None = None
    data_inicio: date | None = None
    sessoes_previstas: int | None = Field(default=None, ge=0)
    status: StatusTratamento | None = None
    situacao_final: str | None = None
    observacao: str | None = None


class TratamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_tratamento_id: int
    tipo_nome: str
    solicitante: PessoaMini | None
    data_inicio: date
    sessoes_previstas: int | None
    # contado a partir dos atendimentos (não é digitado)
    sessoes_realizadas: int
    status: StatusTratamento
    situacao_final: str | None
    observacao: str | None
    criado_em: datetime
    assistidos: list[AssistidoOut]
    evolucoes: list[EvolucaoOut]


class TratamentoListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_tratamento_id: int
    tipo_nome: str
    solicitante: PessoaMini | None
    data_inicio: date
    sessoes_previstas: int | None
    sessoes_realizadas: int
    status: StatusTratamento
    qtd_assistidos: int
    qtd_evolucoes: int


# ---------- histórico da pessoa ----------


class ItemHistorico(BaseModel):
    tipo: Literal["atendimento", "tratamento_inicio", "evolucao"]
    data: date
    titulo: str
    descricao: str | None
    atendimento_id: int | None
    tratamento_id: int | None
    detalhes: dict[str, object] | None = None
