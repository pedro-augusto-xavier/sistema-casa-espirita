"""época de credencial nas sessões

A revogação em massa (UPDATE em sessao_usuario) não pegava a sessão de um
login concorrente que leu a senha/MFA antigos e gravou a sessão depois do
UPDATE (security-audit, achado #5). Agora o usuário tem uma época que muda a
cada troca de senha, ativação/desativação do MFA ou mudança de papel, e a
sessão guarda a época que valia quando o login leu a senha: só vale enquanto
for a mesma.

As sessões que já existem recebem a época atual do dono -- ninguém é
deslogado no deploy.

Revision ID: 8b2e4d6f1a37
Revises: 1352e867c028
Create Date: 2026-11-06 22:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8b2e4d6f1a37"
down_revision: Union[str, None] = "1352e867c028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuario",
        sa.Column(
            "epoca_credencial",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "sessao_usuario",
        sa.Column("epoca_credencial", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE sessao_usuario s SET epoca_credencial = u.epoca_credencial "
        "FROM usuario u WHERE u.id = s.usuario_id"
    )
    op.alter_column("sessao_usuario", "epoca_credencial", nullable=False)


def downgrade() -> None:
    op.drop_column("sessao_usuario", "epoca_credencial")
    op.drop_column("usuario", "epoca_credencial")
