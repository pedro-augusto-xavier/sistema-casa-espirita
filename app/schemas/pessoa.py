"""Formatos de entrada e saída da API para Pessoa (validação com Pydantic)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validators import cpf_valido, normaliza_cep, so_digitos
from app.models.enums import Papel, Sexo

# --- funções de validação reutilizadas nos schemas de entrada ---

def _checa_cpf(v: str | None) -> str | None:
    if v is None or v.strip() == "":
        return None
    digitos = so_digitos(v)
    if not cpf_valido(digitos):
        raise ValueError("CPF inválido")
    return digitos


def _checa_uf(v: str | None) -> str | None:
    if not v:
        return None
    v = v.strip().upper()
    if len(v) != 2 or not v.isalpha():
        raise ValueError("UF deve ter 2 letras")
    return v


def _checa_cep(v: str | None) -> str | None:
    if not v:
        return None
    cep = normaliza_cep(v)
    if cep is None:
        raise ValueError("CEP deve ter 8 dígitos")
    return cep


def _checa_nascimento(v: date | None) -> date | None:
    if v and v > date.today():
        raise ValueError("Data de nascimento não pode ser no futuro")
    return v


def _extrai_papeis(v: object) -> object:
    """Converte list[PessoaPapel] -> list[str] na serialização de saída."""
    if isinstance(v, list) and v and not isinstance(v[0], str):
        return [p.papel for p in v]
    return v


class PessoaMini(BaseModel):
    """Versão enxuta, usada quando uma pessoa aparece dentro de outro recurso."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str


class PessoaBase(BaseModel):
    nome_completo: str = Field(min_length=3, max_length=200)
    data_nascimento: date | None = None
    sexo: Sexo = Sexo.nao_informado

    cpf: str | None = Field(default=None, description="Somente números ou formatado")
    telefone: str | None = Field(default=None, max_length=20)

    logradouro: str | None = Field(default=None, max_length=200)
    numero: str | None = Field(default=None, max_length=20)
    complemento: str | None = Field(default=None, max_length=100)
    bairro: str | None = Field(default=None, max_length=100)
    cidade: str | None = Field(default=None, max_length=100)
    uf: str | None = Field(default=None, max_length=2)
    cep: str | None = Field(default=None, max_length=9)

    como_conheceu: str | None = Field(default=None, max_length=255)
    observacoes_gerais: str | None = None

    _v_cpf = field_validator("cpf")(_checa_cpf)
    _v_uf = field_validator("uf")(_checa_uf)
    _v_cep = field_validator("cep")(_checa_cep)
    _v_nasc = field_validator("data_nascimento")(_checa_nascimento)


class PessoaCreate(PessoaBase):
    consentimento_lgpd: bool = False
    papeis: list[Papel] = Field(default_factory=list)


class PessoaUpdate(BaseModel):
    """Todos os campos opcionais -- só chega o que muda (PATCH)."""

    model_config = ConfigDict(extra="forbid")

    nome_completo: str | None = Field(default=None, min_length=3, max_length=200)
    data_nascimento: date | None = None
    sexo: Sexo | None = None
    cpf: str | None = None
    telefone: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    cep: str | None = None
    como_conheceu: str | None = None
    observacoes_gerais: str | None = None
    consentimento_lgpd: bool | None = None
    papeis: list[Papel] | None = None

    _v_cpf = field_validator("cpf")(_checa_cpf)
    _v_uf = field_validator("uf")(_checa_uf)
    _v_cep = field_validator("cep")(_checa_cep)
    _v_nasc = field_validator("data_nascimento")(_checa_nascimento)


class PessoaListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    telefone: str | None
    cidade: str | None
    uf: str | None
    ativo: bool
    papeis: list[Papel]

    _v_papeis = field_validator("papeis", mode="before")(_extrai_papeis)


class PessoaOut(PessoaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
    anonimizada: bool
    consentimento_lgpd: bool
    consentimento_em: datetime | None
    criado_em: datetime
    atualizado_em: datetime
    papeis: list[Papel]

    _v_papeis = field_validator("papeis", mode="before")(_extrai_papeis)
