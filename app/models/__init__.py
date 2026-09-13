"""Importa todos os modelos num lugar só.

O Alembic e o SQLAlchemy usam este pacote para descobrir todas as tabelas.
Sempre que criar um modelo novo, adicione aqui.
"""

from app.models.agenda import Escala, EventoAgenda
from app.models.atendimento import Atendimento, AtendimentoTratamento
from app.models.pessoa import Pessoa, PessoaPapel, PessoaVinculo
from app.models.trabalhador import FuncaoTrabalhador, TrabalhadorFuncao
from app.models.tratamento import (
    TipoTratamento,
    Tratamento,
    TratamentoAssistido,
    TratamentoEvolucao,
)
from app.models.usuario import AuditLog, Usuario

__all__ = [
    "Escala",
    "EventoAgenda",
    "Atendimento",
    "AtendimentoTratamento",
    "Pessoa",
    "PessoaPapel",
    "PessoaVinculo",
    "FuncaoTrabalhador",
    "TrabalhadorFuncao",
    "TipoTratamento",
    "Tratamento",
    "TratamentoAssistido",
    "TratamentoEvolucao",
    "AuditLog",
    "Usuario",
]
