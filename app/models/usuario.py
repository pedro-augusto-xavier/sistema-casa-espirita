"""Usuário do sistema (quem faz login) e o log de auditoria (LGPD)."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AcaoAuditoria, PapelUsuario


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    papel: Mapped[PapelUsuario] = mapped_column(
        Enum(PapelUsuario, native_enum=False, length=20),
        default=PapelUsuario.operador,
        nullable=False,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLog(Base):
    """Registro de quem fez o quê. Nunca é editado nem apagado."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL")
    )
    acao: Mapped[AcaoAuditoria] = mapped_column(
        Enum(AcaoAuditoria, native_enum=False, length=20), nullable=False
    )
    entidade: Mapped[str] = mapped_column(String(50), nullable=False)
    entidade_id: Mapped[int | None] = mapped_column(Integer)
    dados: Mapped[dict | None] = mapped_column(JSONB)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    usuario: Mapped[Usuario | None] = relationship()

    @property
    def usuario_nome(self) -> str | None:
        return self.usuario.nome if self.usuario else None
