"""Funções que um trabalhador pode exercer (médium, limpeza, apoio...)."""

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FuncaoTrabalhador(Base):
    """Lista de referência, editável pelo admin."""

    __tablename__ = "funcao_trabalhador"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TrabalhadorFuncao(Base):
    """Liga uma pessoa (trabalhador) a uma função."""

    __tablename__ = "trabalhador_funcao"
    __table_args__ = (
        UniqueConstraint("pessoa_id", "funcao_id", name="uq_trabalhador_funcao"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pessoa_id: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id", ondelete="CASCADE"), nullable=False
    )
    funcao_id: Mapped[int] = mapped_column(
        ForeignKey("funcao_trabalhador.id", ondelete="RESTRICT"), nullable=False
    )

    funcao: Mapped[FuncaoTrabalhador] = relationship()
