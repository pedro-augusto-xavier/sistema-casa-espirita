"""Atendimento: a visita avulsa. Uma linha por vez que a pessoa é atendida.
Pode ter vários tratamentos no mesmo dia (passe + conversa fraterna, etc.).
"""

from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Modalidade
from app.models.mixins import TimestampMixin


class Atendimento(TimestampMixin, Base):
    __tablename__ = "atendimento"

    id: Mapped[int] = mapped_column(primary_key=True)

    pessoa_id: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id", ondelete="CASCADE"), nullable=False
    )
    data: Mapped[date] = mapped_column(
        Date, server_default=func.current_date(), nullable=False
    )
    # o médium / trabalhador que atendeu (ex: "Tia Maria")
    atendido_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("pessoa.id", ondelete="SET NULL")
    )
    # quem levou a informação, quando não é a própria pessoa
    solicitante_id: Mapped[int | None] = mapped_column(
        ForeignKey("pessoa.id", ondelete="SET NULL")
    )
    presente: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    modalidade: Mapped[Modalidade] = mapped_column(
        Enum(Modalidade, native_enum=False, length=20),
        default=Modalidade.presencial,
        nullable=False,
    )
    ordem_chegada: Mapped[int | None] = mapped_column(Integer)
    observacao: Mapped[str | None] = mapped_column(Text)
    retorno_previsto: Mapped[date | None] = mapped_column(Date)

    criado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL")
    )

    pessoa: Mapped["object"] = relationship("Pessoa", foreign_keys=[pessoa_id])
    atendido_por: Mapped["object"] = relationship(
        "Pessoa", foreign_keys=[atendido_por_id]
    )
    solicitante: Mapped["object"] = relationship(
        "Pessoa", foreign_keys=[solicitante_id]
    )
    tratamentos: Mapped[list["AtendimentoTratamento"]] = relationship(
        back_populates="atendimento",
        cascade="all, delete-orphan",
        order_by="AtendimentoTratamento.id",
    )

    @property
    def tratamentos_resumo(self) -> list[str]:
        """Nomes dos tratamentos do dia -- usado na listagem."""
        return [t.tipo_tratamento.nome for t in self.tratamentos]


class AtendimentoTratamento(Base):
    """Cada tratamento marcado num atendimento (o 'Reflexologia SIM/NÃO' da ficha)."""

    __tablename__ = "atendimento_tratamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    atendimento_id: Mapped[int] = mapped_column(
        ForeignKey("atendimento.id", ondelete="CASCADE"), nullable=False
    )
    tipo_tratamento_id: Mapped[int] = mapped_column(
        ForeignKey("tipo_tratamento.id", ondelete="RESTRICT"), nullable=False
    )
    # o "P / D" da ficha de papel
    modalidade: Mapped[Modalidade | None] = mapped_column(
        Enum(Modalidade, native_enum=False, length=20)
    )
    sessoes_previstas: Mapped[int | None] = mapped_column(Integer)  # o "7"
    sessoes_realizadas: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    observacao: Mapped[str | None] = mapped_column(Text)

    atendimento: Mapped[Atendimento] = relationship(back_populates="tratamentos")
    tipo_tratamento: Mapped["object"] = relationship("TipoTratamento")

    @property
    def tipo_tratamento_nome(self) -> str:
        return self.tipo_tratamento.nome
