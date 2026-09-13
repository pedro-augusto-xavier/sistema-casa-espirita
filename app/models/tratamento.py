"""Tipos de tratamento e o 'caso' de acompanhamento longo (Desobsessão etc.).

Fluxo:
  - TipoTratamento: a lista (Reflexologia, Desobsessão, Grupo Despertar...).
  - Tratamento: um caso aberto por um solicitante/responsável.
  - TratamentoAssistido: cada pessoa atendida dentro do caso (conclui na sua hora).
  - TratamentoEvolucao: o diário com data que os trabalhadores vão preenchendo.
"""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    FormatoTratamento,
    StatusAssistido,
    StatusTratamento,
    TipoVinculo,
)
from app.models.mixins import TimestampMixin


class TipoTratamento(Base):
    __tablename__ = "tipo_tratamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    formato: Mapped[FormatoTratamento] = mapped_column(
        Enum(FormatoTratamento, native_enum=False, length=20), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Tratamento(TimestampMixin, Base):
    """Caso de tratamento (principalmente Desobsessão), com 1+ assistidos."""

    __tablename__ = "tratamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_tratamento_id: Mapped[int] = mapped_column(
        ForeignKey("tipo_tratamento.id", ondelete="RESTRICT"), nullable=False
    )
    solicitante_id: Mapped[int | None] = mapped_column(
        ForeignKey("pessoa.id", ondelete="SET NULL")
    )
    data_inicio: Mapped[date] = mapped_column(
        Date, server_default=func.current_date(), nullable=False
    )
    sessoes_previstas: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[StatusTratamento] = mapped_column(
        Enum(StatusTratamento, native_enum=False, length=20),
        default=StatusTratamento.em_andamento,
        nullable=False,
    )
    situacao_final: Mapped[str | None] = mapped_column(Text)
    observacao: Mapped[str | None] = mapped_column(Text)
    criado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL")
    )

    tipo: Mapped[TipoTratamento] = relationship()
    solicitante: Mapped["object"] = relationship(
        "Pessoa", foreign_keys=[solicitante_id]
    )
    assistidos: Mapped[list["TratamentoAssistido"]] = relationship(
        back_populates="tratamento",
        cascade="all, delete-orphan",
        order_by="TratamentoAssistido.id",
    )
    evolucoes: Mapped[list["TratamentoEvolucao"]] = relationship(
        back_populates="tratamento",
        cascade="all, delete-orphan",
        order_by="TratamentoEvolucao.data, TratamentoEvolucao.id",
    )

    @property
    def tipo_nome(self) -> str:
        return self.tipo.nome

    @property
    def qtd_assistidos(self) -> int:
        return len(self.assistidos)

    @property
    def qtd_evolucoes(self) -> int:
        return len(self.evolucoes)

    @property
    def sessoes_realizadas(self) -> int:
        """Quantas vezes já vieram por este caso: atendimentos do responsável
        ou dos assistidos, a partir do início, em que este tipo foi marcado.
        É o contador ao lado do "nº vezes" da ficha de papel."""
        from sqlalchemy import distinct, func, select
        from sqlalchemy.orm import object_session

        from app.models.atendimento import Atendimento, AtendimentoTratamento

        db = object_session(self)
        pessoas = [a.pessoa_id for a in self.assistidos]
        if self.solicitante_id is not None:
            pessoas.append(self.solicitante_id)
        if db is None or not pessoas:
            return 0
        stmt = (
            select(func.count(distinct(Atendimento.id)))
            .join(Atendimento.tratamentos)
            .where(
                Atendimento.pessoa_id.in_(pessoas),
                Atendimento.data >= self.data_inicio,
                AtendimentoTratamento.tipo_tratamento_id == self.tipo_tratamento_id,
            )
        )
        return db.scalar(stmt) or 0


class TratamentoAssistido(Base):
    __tablename__ = "tratamento_assistido"
    __table_args__ = (
        UniqueConstraint(
            "tratamento_id", "pessoa_id", name="uq_tratamento_assistido"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(
        ForeignKey("tratamento.id", ondelete="CASCADE"), nullable=False
    )
    pessoa_id: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[StatusAssistido] = mapped_column(
        Enum(StatusAssistido, native_enum=False, length=20),
        default=StatusAssistido.ativo,
        nullable=False,
    )
    situacao_final: Mapped[str | None] = mapped_column(Text)
    data_conclusao: Mapped[date | None] = mapped_column(Date)
    # o quê essa pessoa é do responsável (filho, amigo...). Nulo quando o
    # assistido é o próprio responsável -- não faz sentido ter vínculo consigo.
    vinculo_com_responsavel: Mapped[TipoVinculo | None] = mapped_column(
        Enum(TipoVinculo, native_enum=False, length=20)
    )

    tratamento: Mapped[Tratamento] = relationship(back_populates="assistidos")
    pessoa: Mapped["object"] = relationship("Pessoa")


class TratamentoEvolucao(Base):
    """Cada linha do diário: data + texto, escrita por um trabalhador."""

    __tablename__ = "tratamento_evolucao"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(
        ForeignKey("tratamento.id", ondelete="CASCADE"), nullable=False
    )
    data: Mapped[date] = mapped_column(
        Date, server_default=func.current_date(), nullable=False
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    # quem anotou (trabalhador)
    registrado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("pessoa.id", ondelete="SET NULL")
    )
    # opcional: a qual assistido essa nota se refere
    pessoa_id: Mapped[int | None] = mapped_column(
        ForeignKey("pessoa.id", ondelete="SET NULL")
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tratamento: Mapped[Tratamento] = relationship(back_populates="evolucoes")
    registrado_por: Mapped["object"] = relationship(
        "Pessoa", foreign_keys=[registrado_por_id]
    )
    pessoa: Mapped["object"] = relationship("Pessoa", foreign_keys=[pessoa_id])
