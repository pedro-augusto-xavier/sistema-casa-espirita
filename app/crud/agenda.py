"""Acesso ao banco para EventoAgenda e Escala."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NaoEncontrado
from app.models.agenda import Escala, EventoAgenda
from app.models.enums import TipoEvento
from app.models.pessoa import Pessoa
from app.schemas.agenda import EscalaIn, EventoAgendaCreate, EventoAgendaUpdate

_CARREGAR_TUDO = (selectinload(EventoAgenda.escalas).selectinload(Escala.pessoa),)


def get(db: Session, evento_id: int) -> EventoAgenda | None:
    stmt = (
        select(EventoAgenda)
        .options(*_CARREGAR_TUDO)
        .where(EventoAgenda.id == evento_id)
    )
    return db.scalar(stmt)


def listar(
    db: Session,
    *,
    tipo: TipoEvento | None = None,
    de: datetime | None = None,
    ate: datetime | None = None,
    apenas_ativos: bool = True,
    page: int = 1,
    size: int = 20,
) -> tuple[list[EventoAgenda], int]:
    stmt = select(EventoAgenda).options(*_CARREGAR_TUDO)

    if apenas_ativos:
        stmt = stmt.where(EventoAgenda.ativo.is_(True))
    if tipo is not None:
        stmt = stmt.where(EventoAgenda.tipo == tipo)
    if de is not None:
        stmt = stmt.where(EventoAgenda.data_inicio >= de)
    if ate is not None:
        stmt = stmt.where(EventoAgenda.data_inicio <= ate)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(EventoAgenda.data_inicio)
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(stmt).all()), total


def _pessoa_ou_erro(db: Session, pessoa_id: int, campo: str) -> None:
    if db.get(Pessoa, pessoa_id) is None:
        raise NaoEncontrado(f"{campo}: pessoa {pessoa_id} não existe")


def _monta_escalas(db: Session, itens: list[EscalaIn]) -> list[Escala]:
    ids = {i.pessoa_id for i in itens}
    existentes = set(db.scalars(select(Pessoa.id).where(Pessoa.id.in_(ids))).all())
    faltando = ids - existentes
    if faltando:
        raise NaoEncontrado(f"pessoa(s) inexistente(s): {sorted(faltando)}")

    funcao_por_pessoa = {i.pessoa_id: i.funcao for i in itens}
    return [
        Escala(pessoa_id=pid, funcao=funcao_por_pessoa[pid]) for pid in ids
    ]


def criar(db: Session, dados: EventoAgendaCreate) -> EventoAgenda:
    evento = EventoAgenda(
        titulo=dados.titulo,
        tipo=dados.tipo,
        data_inicio=dados.data_inicio,
        data_fim=dados.data_fim,
        recorrencia=dados.recorrencia,
        descricao=dados.descricao,
    )
    evento.escalas = _monta_escalas(db, dados.escalados)

    db.add(evento)
    db.commit()
    return get(db, evento.id)  # type: ignore[return-value]


def atualizar(
    db: Session, evento: EventoAgenda, dados: EventoAgendaUpdate
) -> EventoAgenda:
    mudancas = dados.model_dump(exclude_unset=True, exclude={"escalados"})
    for campo, valor in mudancas.items():
        setattr(evento, campo, valor)

    if dados.escalados is not None:
        evento.escalas = _monta_escalas(db, dados.escalados)

    db.commit()
    return get(db, evento.id)  # type: ignore[return-value]


def remover(db: Session, evento: EventoAgenda) -> None:
    db.delete(evento)
    db.commit()
