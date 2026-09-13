"""Anexo: um arquivo (foto, PDF) que a equipe recebe e guarda.

Sempre pertence a uma pessoa (aparece na ficha dela) e, opcionalmente, está
ligado a um item específico do histórico -- um atendimento ou um tratamento
-- pra não virar uma pilha solta de arquivos sem contexto.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Anexo(Base):
    __tablename__ = "anexo"
    __table_args__ = (
        CheckConstraint(
            "NOT (atendimento_id IS NOT NULL AND tratamento_id IS NOT NULL)",
            name="ck_anexo_um_so_vinculo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pessoa_id: Mapped[int] = mapped_column(
        ForeignKey("pessoa.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # opcional: prende o anexo a um item específico do histórico da pessoa
    atendimento_id: Mapped[int | None] = mapped_column(
        ForeignKey("atendimento.id", ondelete="CASCADE")
    )
    tratamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("tratamento.id", ondelete="CASCADE")
    )

    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_conteudo: Mapped[str] = mapped_column(String(100), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    # carregado só quando pedido explicitamente (ver crud.anexo.get) -- listar
    # não precisa trazer o arquivo inteiro pra memória.
    conteudo: Mapped[bytes] = mapped_column(LargeBinary, nullable=False, deferred=True)
    descricao: Mapped[str | None] = mapped_column(Text)

    enviado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL")
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    pessoa: Mapped["object"] = relationship("Pessoa")
    enviado_por: Mapped["object"] = relationship("Usuario")

    @property
    def enviado_por_nome(self) -> str | None:
        return self.enviado_por.nome if self.enviado_por else None
