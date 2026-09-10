"""Agenda: palestras, dias de trabalho, encontros de grupo -- e quem está escalado."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TipoEvento


class EventoAgenda(Base):
    __tablename__ = "evento_agenda"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[TipoEvento] = mapped_column(
        Enum(TipoEvento, native_enum=False, length=20), nullable=False
    )
    data_inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    data_fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # ex: "semanal:terca" -- por enquanto texto simples
    recorrencia: Mapped[str | None] = mapped_column(String(50))
    descricao: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    escalas: Mapped[list["Escala"]] = relationship(
        back_populates="evento", cascade="all, delete-orphan"
    )


class Escala(Base):
    """Quem trabalha em determinado evento/dia."""

    __tablename__ = "escala"
    __table_args__ = (
        UniqueConstraint("evento_id", "pessoa_id", name="uq_escala"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    evento_id: Mapped[int] = mapped_column(
        ForeignKey("evento_agenda.id", ondelete="CASCADE"), nullable=False
    )
    pessoa_id: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id", ondelete="CASCADE"), nullable=False
    )
    funcao: Mapped[str | None] = mapped_column(String(80))

    evento: Mapped[EventoAgenda] = relationship(back_populates="escalas")
    pessoa: Mapped["object"] = relationship("Pessoa")
