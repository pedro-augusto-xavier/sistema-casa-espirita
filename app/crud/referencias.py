"""Leitura das listas de referência."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import FormatoTratamento
from app.models.trabalhador import FuncaoTrabalhador
from app.models.tratamento import TipoTratamento


def listar_tipos_tratamento(
    db: Session,
    *,
    formato: FormatoTratamento | None = None,
    apenas_ativos: bool = True,
) -> list[TipoTratamento]:
    stmt = select(TipoTratamento)
    if apenas_ativos:
        stmt = stmt.where(TipoTratamento.ativo.is_(True))
    if formato is not None:
        stmt = stmt.where(TipoTratamento.formato == formato)
    stmt = stmt.order_by(TipoTratamento.nome)
    return list(db.scalars(stmt).all())


def get_tipo_tratamento(db: Session, tipo_id: int) -> TipoTratamento | None:
    return db.get(TipoTratamento, tipo_id)


def listar_funcoes(
    db: Session, *, apenas_ativos: bool = True
) -> list[FuncaoTrabalhador]:
    stmt = select(FuncaoTrabalhador)
    if apenas_ativos:
        stmt = stmt.where(FuncaoTrabalhador.ativo.is_(True))
    stmt = stmt.order_by(FuncaoTrabalhador.nome)
    return list(db.scalars(stmt).all())
