"""Usuário do sistema (quem faz login), as sessões abertas e o log de
auditoria (LGPD)."""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.cripto import TextoCifrado
from app.core.database import Base
from app.models.enums import AcaoAuditoria, PapelUsuario

# o que falta a pessoa fazer antes de poder usar o sistema
PENDENCIA_TROCAR_SENHA = "trocar_senha"
PENDENCIA_CONFIGURAR_MFA = "configurar_mfa"


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        # login é pelo nome -- só precisa ser único entre quem está ativo
        # (um ex-funcionário desligado não trava o nome pra quem entrar
        # depois). Comparação ignora maiúscula/minúscula.
        Index(
            "uq_usuario_nome_ativo",
            text("lower(nome)"),
            unique=True,
            postgresql_where=text("ativo = true"),
        ),
        # e-mail é só um contato opcional agora -- quando preenchido, não
        # pode repetir.
        Index(
            "uq_usuario_email",
            "email",
            unique=True,
            postgresql_where=text("email IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
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

    # Senha aleatória gerada pelo servidor quando o admin cria ou redefine o
    # usuário -- vale só pro primeiro acesso (a pessoa é obrigada a criar uma
    # senha própria) e só até senha_provisoria_expira_em.
    senha_provisoria: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    senha_provisoria_expira_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    senha_alterada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    ultimo_login_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Verificação em duas etapas (TOTP). O segredo fica cifrado como o CPF.
    mfa_segredo: Mapped[str | None] = mapped_column(
        TextoCifrado("usuario.mfa_segredo")
    )
    mfa_ativo: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    # último código aceito (o "passo" de 30s) -- impede reusar o mesmo código
    mfa_ultimo_passo: Mapped[int | None] = mapped_column(Integer)

    @property
    def mfa_obrigatorio(self) -> bool:
        if settings.MFA_OBRIGATORIO == "todos":
            return True
        if settings.MFA_OBRIGATORIO == "admin":
            return self.papel == PapelUsuario.admin
        return False

    @property
    def senha_provisoria_vencida(self) -> bool:
        """Senha provisória que passou da validade (ou sem validade gravada)
        não serve mais: nem pra entrar, nem pra continuar numa sessão aberta
        com ela. Só o admin redefinindo resolve."""
        if not self.senha_provisoria:
            return False
        expira = self.senha_provisoria_expira_em
        return expira is None or datetime.now(UTC) >= expira

    @property
    def pendencias(self) -> list[str]:
        """O que a pessoa precisa resolver antes de liberar o resto do
        sistema. Enquanto tiver pendência, a API só aceita as rotas de
        /auth (ver api/deps.py)."""
        lista = []
        if self.senha_provisoria:
            lista.append(PENDENCIA_TROCAR_SENHA)
        if self.mfa_obrigatorio and not self.mfa_ativo:
            lista.append(PENDENCIA_CONFIGURAR_MFA)
        return lista


class SessaoUsuario(Base):
    """Cada login abre uma sessão. O token só vale enquanto a sessão existir
    e não estiver revogada -- assim "Sair", trocar a senha ou desativar o
    usuário cortam o acesso na hora, e não só quando o token expirar."""

    __tablename__ = "sessao_usuario"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, index=True
    )
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expira_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ultimo_uso_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revogada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))

    usuario: Mapped[Usuario] = relationship()


class AuditLog(Base):
    """Registro de quem fez o quê. Nunca é editado nem apagado -- o banco
    recusa UPDATE e DELETE nesta tabela (trigger, ver migration)."""

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
    ip: Mapped[str | None] = mapped_column(String(64))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    usuario: Mapped[Usuario | None] = relationship()

    @property
    def usuario_nome(self) -> str | None:
        return self.usuario.nome if self.usuario else None
