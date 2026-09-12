"""Acesso ao banco para Atendimento (a visita avulsa)."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NaoEncontrado
from app.models.atendimento import Atendimento, AtendimentoTratamento
from app.models.pessoa import Pessoa
from app.models.tratamento import TipoTratamento
from app.schemas.atendimento import (
    AtendimentoCreate,
    AtendimentoTratamentoIn,
    AtendimentoUpdate,
)

_CARREGAR_TUDO = (
    selectinload(Atendimento.pessoa).selectinload(Pessoa.papeis),
    selectinload(Atendimento.atendido_por),
    selectinload(Atendimento.solicitante),
    selectinload(Atendimento.tratamentos).selectinload(
        AtendimentoTratamento.tipo_tratamento
    ),
)


def get(db: Session, atendimento_id: int) -> Atendimento | None:
    stmt = (
        select(Atendimento)
        .options(*_CARREGAR_TUDO)
        .where(Atendimento.id == atendimento_id)
    )
    return db.scalar(stmt)


def listar(
    db: Session,
    *,
    pessoa_id: int | None = None,
    atendido_por_id: int | None = None,
    de: date | None = None,
    ate: date | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Atendimento], int]:
    stmt = select(Atendimento).options(*_CARREGAR_TUDO)

    if pessoa_id is not None:
        stmt = stmt.where(Atendimento.pessoa_id == pessoa_id)
    if atendido_por_id is not None:
        stmt = stmt.where(Atendimento.atendido_por_id == atendido_por_id)
    if de is not None:
        stmt = stmt.where(Atendimento.data >= de)
    if ate is not None:
        stmt = stmt.where(Atendimento.data <= ate)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(Atendimento.data.desc(), Atendimento.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(stmt).all()), total


def _checa_pessoa(db: Session, pessoa_id: int | None, campo: str) -> None:
    if pessoa_id is None:
        return
    if db.get(Pessoa, pessoa_id) is None:
        raise NaoEncontrado(f"{campo}: pessoa {pessoa_id} não existe")


def _monta_tratamentos(
    db: Session, itens: list[AtendimentoTratamentoIn]
) -> list[AtendimentoTratamento]:
    ids = {i.tipo_tratamento_id for i in itens}
    existentes = set(
        db.scalars(
            select(TipoTratamento.id).where(TipoTratamento.id.in_(ids))
        ).all()
    )
    faltando = ids - existentes
    if faltando:
        raise NaoEncontrado(
            f"tipo(s) de tratamento inexistente(s): {sorted(faltando)}"
        )
    return [
        AtendimentoTratamento(
            tipo_tratamento_id=i.tipo_tratamento_id,
            modalidade=i.modalidade,
            sessoes_previstas=i.sessoes_previstas,
            sessoes_realizadas=i.sessoes_realizadas,
            observacao=i.observacao,
        )
        for i in itens
    ]


def criar(db: Session, dados: AtendimentoCreate) -> Atendimento:
    _checa_pessoa(db, dados.pessoa_id, "pessoa_id")
    _checa_pessoa(db, dados.atendido_por_id, "atendido_por_id")
    _checa_pessoa(db, dados.solicitante_id, "solicitante_id")

    payload = dados.model_dump(exclude={"tratamentos", "data"})
    atendimento = Atendimento(**payload)
    if dados.data is not None:
        atendimento.data = dados.data

    atendimento.tratamentos = _monta_tratamentos(db, dados.tratamentos)

    db.add(atendimento)
    db.commit()
    return get(db, atendimento.id)  # type: ignore[return-value]


def atualizar(
    db: Session, atendimento: Atendimento, dados: AtendimentoUpdate
) -> Atendimento:
    mudancas = dados.model_dump(exclude_unset=True, exclude={"tratamentos"})

    for campo in ("atendido_por_id", "solicitante_id"):
        if campo in mudancas:
            _checa_pessoa(db, mudancas[campo], campo)

    for campo, valor in mudancas.items():
        setattr(atendimento, campo, valor)

    if dados.tratamentos is not None:
        atendimento.tratamentos = _monta_tratamentos(db, dados.tratamentos)

    db.commit()
    return get(db, atendimento.id)  # type: ignore[return-value]


def remover(db: Session, atendimento: Atendimento) -> None:
    db.delete(atendimento)
    db.commit()
