"""Leitura do log de auditoria (só admin usa)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.usuario import AuditLog


def listar(
    db: Session,
    *,
    entidade: str | None = None,
    entidade_id: int | None = None,
    usuario_id: int | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[AuditLog], int]:
    stmt = select(AuditLog).options(selectinload(AuditLog.usuario))

    if entidade is not None:
        stmt = stmt.where(AuditLog.entidade == entidade)
    if entidade_id is not None:
        stmt = stmt.where(AuditLog.entidade_id == entidade_id)
    if usuario_id is not None:
        stmt = stmt.where(AuditLog.usuario_id == usuario_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(AuditLog.criado_em.desc(), AuditLog.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(stmt).all()), total
