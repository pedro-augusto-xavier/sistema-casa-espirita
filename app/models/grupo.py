"""Sessões de grupo (Grupo Despertar, Grupo de Estudos) e a presença avulsa."""

from datetime import date

from sqlalchemy import Date, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SessaoGrupo(Base):
    __tablename__ = "sessao_grupo"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_tratamento_id: Mapped[int] = mapped_column(
        ForeignKey("tipo_tratamento.id", ondelete="RESTRICT"), nullable=False
    )
    data: Mapped[date] = mapped_column(
        Date, server_default=func.current_date(), nullable=False
    )
    responsavel_id: Mapped[int | None] = mapped_column(
        ForeignKey("pessoa.id", ondelete="SET NULL")
    )
    observacao: Mapped[str | None] = mapped_column(Text)

    tipo_tratamento: Mapped["object"] = relationship("TipoTratamento")
    responsavel: Mapped["object"] = relationship(
        "Pessoa", foreign_keys=[responsavel_id]
    )
    presencas: Mapped[list["Presenca"]] = relationship(
        back_populates="sessao", cascade="all, delete-orphan", order_by="Presenca.id"
    )

    @property
    def tipo_nome(self) -> str:
        return self.tipo_tratamento.nome

    @property
    def qtd_presentes(self) -> int:
        return len(self.presencas)


class Presenca(Base):
    __tablename__ = "presenca"
    __table_args__ = (
        UniqueConstraint("sessao_grupo_id", "pessoa_id", name="uq_presenca"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sessao_grupo_id: Mapped[int] = mapped_column(
        ForeignKey("sessao_grupo.id", ondelete="CASCADE"), nullable=False
    )
    pessoa_id: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id", ondelete="CASCADE"), nullable=False
    )

    sessao: Mapped[SessaoGrupo] = relationship(back_populates="presencas")
    pessoa: Mapped["object"] = relationship("Pessoa")
