"""Pessoa: a ficha de cadastro. Serve para todo mundo -- trabalhador,
quem é atendido e quem leva a informação de outra pessoa.
"""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.cripto import TextoCifrado, hmac_busca
from app.core.database import Base
from app.models.enums import EstadoCivil, Papel, Sexo, TipoVinculo
from app.models.mixins import TimestampMixin


class Pessoa(TimestampMixin, Base):
    __tablename__ = "pessoa"
    __table_args__ = (
        # CPF é opcional, mas quando preenchido não pode repetir. Como o CPF
        # fica cifrado, a unicidade é conferida pelo HMAC dele.
        Index(
            "uq_pessoa_cpf_hash",
            "cpf_hash",
            unique=True,
            postgresql_where=text("cpf_hash IS NOT NULL"),
        ),
        CheckConstraint(
            "quantidade_filhos IS NULL OR quantidade_filhos >= 0",
            name="ck_pessoa_quantidade_filhos_positiva",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    nome_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    sexo: Mapped[Sexo] = mapped_column(
        Enum(Sexo, native_enum=False, length=20),
        default=Sexo.nao_informado,
        nullable=False,
    )
    # CPF cifrado (AES-256-GCM) -- no banco é só bytes. Pra achar duplicado
    # ou buscar pelo CPF completo usa-se `cpf_hash`, que é atualizado sozinho
    # quando `cpf` muda (ver _sincroniza_hash_do_cpf).
    cpf: Mapped[str | None] = mapped_column(
        "cpf_cifrado", TextoCifrado("pessoa.cpf")
    )
    cpf_hash: Mapped[str | None] = mapped_column(String(64))
    telefone: Mapped[str | None] = mapped_column(String(20))
    estado_civil: Mapped[EstadoCivil] = mapped_column(
        Enum(EstadoCivil, native_enum=False, length=20),
        default=EstadoCivil.nao_informado,
        server_default=EstadoCivil.nao_informado.value,
        nullable=False,
    )
    # None = não perguntado ainda; 0 = perguntado e não tem.
    quantidade_filhos: Mapped[int | None] = mapped_column(Integer)

    # Endereço
    logradouro: Mapped[str | None] = mapped_column(String(200))
    numero: Mapped[str | None] = mapped_column(String(20))
    complemento: Mapped[str | None] = mapped_column(String(100))
    bairro: Mapped[str | None] = mapped_column(String(100))
    cidade: Mapped[str | None] = mapped_column(String(100))
    uf: Mapped[str | None] = mapped_column(String(2))
    cep: Mapped[str | None] = mapped_column(String(9))

    como_conheceu: Mapped[str | None] = mapped_column(String(255))
    # pode ter saúde, religião, família -- cifrado
    observacoes_gerais: Mapped[str | None] = mapped_column(
        TextoCifrado("pessoa.observacoes_gerais")
    )

    # LGPD -- dado de religião é sensível
    consentimento_lgpd: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    consentimento_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # Exclusão lógica (nunca apagamos de fato na hora)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # LGPD -- "direito ao esquecimento": dados pessoais apagados, ficha mantida
    # só para não deixar atendimentos órfãos.
    anonimizada: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    papeis: Mapped[list["PessoaPapel"]] = relationship(
        back_populates="pessoa", cascade="all, delete-orphan"
    )
    vinculos: Mapped[list["PessoaVinculo"]] = relationship(
        back_populates="pessoa",
        foreign_keys="PessoaVinculo.pessoa_id",
        cascade="all, delete-orphan",
    )

    @validates("cpf")
    def _sincroniza_hash_do_cpf(self, _chave: str, valor: str | None) -> str | None:
        self.cpf_hash = hmac_busca(valor) if valor else None
        return valor

    def __repr__(self) -> str:  # ajuda no console
        return f"<Pessoa {self.id} {self.nome_completo!r}>"


class PessoaPapel(Base):
    """Marca se a pessoa é trabalhadora, assistida, ou os dois."""

    __tablename__ = "pessoa_papel"
    __table_args__ = (UniqueConstraint("pessoa_id", "papel", name="uq_pessoa_papel"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    pessoa_id: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id", ondelete="CASCADE"), nullable=False
    )
    papel: Mapped[Papel] = mapped_column(
        Enum(Papel, native_enum=False, length=20), nullable=False
    )

    pessoa: Mapped[Pessoa] = relationship(back_populates="papeis")


class PessoaVinculo(Base):
    """Parentesco / relação entre duas pessoas (mãe-filho, amigo, responsável...)."""

    __tablename__ = "pessoa_vinculo"
    __table_args__ = (
        UniqueConstraint(
            "pessoa_id", "relacionado_id", "tipo", name="uq_pessoa_vinculo"
        ),
        CheckConstraint(
            "pessoa_id <> relacionado_id", name="ck_vinculo_pessoas_diferentes"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pessoa_id: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id", ondelete="CASCADE"), nullable=False
    )
    relacionado_id: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[TipoVinculo] = mapped_column(
        Enum(TipoVinculo, native_enum=False, length=20), nullable=False
    )
    descricao: Mapped[str | None] = mapped_column(String(255))

    pessoa: Mapped[Pessoa] = relationship(
        back_populates="vinculos", foreign_keys=[pessoa_id]
    )
    relacionado: Mapped[Pessoa] = relationship(foreign_keys=[relacionado_id])
