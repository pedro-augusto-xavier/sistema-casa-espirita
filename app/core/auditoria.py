"""Registro de auditoria: quem fez o quê.

As rotas de escrita chamam `registrar(...)` depois de uma operação bem-sucedida.
As linhas de audit_log nunca são editadas nem apagadas.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import AcaoAuditoria
from app.models.usuario import AuditLog, Usuario


def registrar(
    db: Session,
    *,
    usuario: Usuario | None,
    acao: AcaoAuditoria,
    entidade: str,
    entidade_id: int | None = None,
    dados: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            usuario_id=usuario.id if usuario else None,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            dados=dados,
        )
    )
    db.commit()
