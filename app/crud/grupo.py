"""Acesso ao banco para SessaoGrupo (Grupo Despertar, Grupo de Estudos)."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NaoEncontrado
from app.models.grupo import Presenca, SessaoGrupo
from app.models.pessoa import Pessoa
from app.models.tratamento import TipoTratamento
from app.schemas.grupo import PresencaIn, SessaoGrupoCreate, SessaoGrupoUpdate

_CARREGAR_TUDO = (
    selectinload(SessaoGrupo.tipo_tratamento),
    selectinload(SessaoGrupo.responsavel),
    selectinload(SessaoGrupo.presencas).selectinload(Presenca.pessoa),
)


def get(db: Session, sessao_id: int) -> SessaoGrupo | None:
    stmt = (
        select(SessaoGrupo).options(*_CARREGAR_TUDO).where(SessaoGrupo.id == sessao_id)
    )
    return db.scalar(stmt)


def listar(
    db: Session,
    *,
    tipo_tratamento_id: int | None = None,
    de: date | None = None,
    ate: date | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[SessaoGrupo], int]:
    stmt = select(SessaoGrupo).options(*_CARREGAR_TUDO)

    if tipo_tratamento_id is not None:
        stmt = stmt.where(SessaoGrupo.tipo_tratamento_id == tipo_tratamento_id)
    if de is not None:
        stmt = stmt.where(SessaoGrupo.data >= de)
    if ate is not None:
        stmt = stmt.where(SessaoGrupo.data <= ate)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(SessaoGrupo.data.desc(), SessaoGrupo.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(stmt).all()), total


def _pessoa_ou_erro(db: Session, pessoa_id: int, campo: str) -> None:
    if db.get(Pessoa, pessoa_id) is None:
        raise NaoEncontrado(f"{campo}: pessoa {pessoa_id} não existe")


def _monta_presencas(db: Session, itens: list[PresencaIn]) -> list[Presenca]:
    ids = {i.pessoa_id for i in itens}
    existentes = set(db.scalars(select(Pessoa.id).where(Pessoa.id.in_(ids))).all())
    faltando = ids - existentes
    if faltando:
        raise NaoEncontrado(f"pessoa(s) inexistente(s): {sorted(faltando)}")
    return [Presenca(pessoa_id=pid) for pid in ids]


def criar(db: Session, dados: SessaoGrupoCreate) -> SessaoGrupo:
    if db.get(TipoTratamento, dados.tipo_tratamento_id) is None:
        raise NaoEncontrado(
            f"tipo de tratamento {dados.tipo_tratamento_id} não existe"
        )
    if dados.responsavel_id is not None:
        _pessoa_ou_erro(db, dados.responsavel_id, "responsavel_id")

    sessao = SessaoGrupo(
        tipo_tratamento_id=dados.tipo_tratamento_id,
        responsavel_id=dados.responsavel_id,
        observacao=dados.observacao,
    )
    if dados.data is not None:
        sessao.data = dados.data

    sessao.presencas = _monta_presencas(db, dados.presentes)

    db.add(sessao)
    db.commit()
    return get(db, sessao.id)  # type: ignore[return-value]


def atualizar(
    db: Session, sessao: SessaoGrupo, dados: SessaoGrupoUpdate
) -> SessaoGrupo:
    mudancas = dados.model_dump(exclude_unset=True, exclude={"presentes"})

    if "responsavel_id" in mudancas and mudancas["responsavel_id"] is not None:
        _pessoa_ou_erro(db, mudancas["responsavel_id"], "responsavel_id")

    for campo, valor in mudancas.items():
        setattr(sessao, campo, valor)

    if dados.presentes is not None:
        sessao.presencas = _monta_presencas(db, dados.presentes)

    db.commit()
    return get(db, sessao.id)  # type: ignore[return-value]


def remover(db: Session, sessao: SessaoGrupo) -> None:
    db.delete(sessao)
    db.commit()
