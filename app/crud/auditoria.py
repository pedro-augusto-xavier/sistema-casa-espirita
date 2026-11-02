"""Leitura do log de auditoria (só admin usa)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import AcaoAuditoria
from app.models.usuario import AuditLog

# Acima disso em 24h, a tela de auditoria acende o alerta
LIMITE_FALHAS_LOGIN_24H = 10
# "fora de hora" no horário de Brasília (UTC-3): antes das 6h ou depois das 23h
_FUSO_BRASILIA = timedelta(hours=-3)


def listar(
    db: Session,
    *,
    entidade: str | None = None,
    entidade_id: int | None = None,
    usuario_id: int | None = None,
    acao: AcaoAuditoria | None = None,
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
    if acao is not None:
        stmt = stmt.where(AuditLog.acao == acao)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(AuditLog.criado_em.desc(), AuditLog.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(stmt).all()), total


def alertas(db: Session) -> dict[str, int | bool]:
    agora = datetime.now(UTC)
    dia = agora - timedelta(hours=24)
    semana = agora - timedelta(days=7)

    falhas = db.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.acao == AcaoAuditoria.login_falha, AuditLog.criado_em >= dia)
    ) or 0
    contas = db.scalar(
        select(func.count(func.distinct(AuditLog.entidade_id))).where(
            AuditLog.acao == AcaoAuditoria.login_falha,
            AuditLog.criado_em >= dia,
            AuditLog.entidade_id.is_not(None),
        )
    ) or 0
    exportacoes = db.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.acao == AcaoAuditoria.exportar, AuditLog.criado_em >= semana)
    ) or 0
    cpfs = db.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.acao == AcaoAuditoria.visualizar, AuditLog.criado_em >= semana)
    ) or 0

    logins = db.scalars(
        select(AuditLog.criado_em).where(
            AuditLog.acao.in_([AcaoAuditoria.login, AcaoAuditoria.exportar]),
            AuditLog.criado_em >= semana,
        )
    ).all()
    fora_de_hora = sum(
        1 for quando in logins if not 6 <= (quando + _FUSO_BRASILIA).hour < 23
    )

    return {
        "falhas_login_24h": falhas,
        "contas_com_falhas_24h": contas,
        "exportacoes_7d": exportacoes,
        "cpfs_vistos_7d": cpfs,
        "acessos_fora_de_hora_7d": fora_de_hora,
        "alerta": falhas >= LIMITE_FALHAS_LOGIN_24H or fora_de_hora > 0,
    }
