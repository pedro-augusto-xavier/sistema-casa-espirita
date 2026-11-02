"""segurança: sessões no servidor, verificação em duas etapas, senha
provisória e IP na auditoria

- sessao_usuario: cada login vira uma sessão; sair/trocar senha/desativar
  usuário corta o acesso na hora.
- usuario: senha_provisoria, mfa_*, ultimo_login_em, senha_alterada_em.
- audit_log.ip: de onde veio cada ação.
- Quem já tinha acesso passa a ter a senha marcada como provisória: no
  próximo login cria uma senha nova, já seguindo as regras novas (10+
  caracteres, nada de CPF/nome/senha manjada).

Revision ID: 0adbab7209a9
Revises: c8985d0345aa
Create Date: 2026-11-02 19:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0adbab7209a9"
down_revision: Union[str, None] = "c8985d0345aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuario",
        sa.Column(
            "senha_provisoria",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "usuario", sa.Column("senha_alterada_em", sa.DateTime(timezone=True))
    )
    op.add_column("usuario", sa.Column("ultimo_login_em", sa.DateTime(timezone=True)))
    op.add_column("usuario", sa.Column("mfa_segredo", sa.LargeBinary()))
    op.add_column(
        "usuario",
        sa.Column(
            "mfa_ativo", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.add_column("usuario", sa.Column("mfa_ultimo_passo", sa.Integer()))

    op.add_column("audit_log", sa.Column("ip", sa.String(length=64)))

    op.create_table(
        "sessao_usuario",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column(
            "criada_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultimo_uso_em", sa.DateTime(timezone=True)),
        sa.Column("revogada_em", sa.DateTime(timezone=True)),
        sa.Column("ip", sa.String(length=64)),
        sa.Column("user_agent", sa.String(length=255)),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sessao_usuario_usuario_id"), "sessao_usuario", ["usuario_id"]
    )

    # regras novas de senha valem pra todo mundo a partir do próximo login
    op.execute("UPDATE usuario SET senha_provisoria = true WHERE ativo = true")


def downgrade() -> None:
    op.drop_index(op.f("ix_sessao_usuario_usuario_id"), table_name="sessao_usuario")
    op.drop_table("sessao_usuario")
    op.drop_column("audit_log", "ip")
    op.drop_column("usuario", "mfa_ultimo_passo")
    op.drop_column("usuario", "mfa_ativo")
    op.drop_column("usuario", "mfa_segredo")
    op.drop_column("usuario", "ultimo_login_em")
    op.drop_column("usuario", "senha_alterada_em")
    op.drop_column("usuario", "senha_provisoria")
