"""Listas de valores fixos usadas nas tabelas.

Usamos enum do Python + Enum(native_enum=False) do SQLAlchemy: no banco isso
vira um VARCHAR com CHECK (mais fácil de alterar depois do que um TYPE nativo).
"""

import enum


class Sexo(str, enum.Enum):
    masculino = "masculino"
    feminino = "feminino"
    outro = "outro"
    nao_informado = "nao_informado"


class Papel(str, enum.Enum):
    """Papel de uma PESSOA dentro da casa (pode ter mais de um)."""

    trabalhador = "trabalhador"
    assistido = "assistido"
    voluntario = "voluntario"


class EstadoCivil(str, enum.Enum):
    solteiro = "solteiro"
    casado = "casado"
    uniao_estavel = "uniao_estavel"
    divorciado = "divorciado"
    viuvo = "viuvo"
    nao_informado = "nao_informado"


class TipoVinculo(str, enum.Enum):
    pai = "pai"
    mae = "mae"
    filho = "filho"
    filha = "filha"
    conjuge = "conjuge"
    irmao = "irmao"
    avo = "avo"
    neto = "neto"
    amigo = "amigo"
    responsavel = "responsavel"
    outro = "outro"


class FormatoTratamento(str, enum.Enum):
    individual = "individual"  # ex: Reflexologia, Energização
    grupo = "grupo"            # ex: Grupo Despertar, Grupo de Estudos
    caso = "caso"              # ex: Desobsessão (acompanhamento longo)


class Modalidade(str, enum.Enum):
    presencial = "presencial"
    video = "video"
    distancia = "distancia"


class StatusTratamento(str, enum.Enum):
    em_andamento = "em_andamento"
    concluido = "concluido"


class StatusAssistido(str, enum.Enum):
    ativo = "ativo"
    concluido = "concluido"
    removido = "removido"


class TipoEvento(str, enum.Enum):
    palestra = "palestra"
    trabalho = "trabalho"
    grupo = "grupo"
    outro = "outro"


class PapelUsuario(str, enum.Enum):
    admin = "admin"
    operador = "operador"


class AcaoAuditoria(str, enum.Enum):
    criar = "criar"
    atualizar = "atualizar"
    excluir = "excluir"
    login = "login"
