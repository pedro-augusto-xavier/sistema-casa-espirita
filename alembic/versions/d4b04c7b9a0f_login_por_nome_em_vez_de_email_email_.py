"""login por nome em vez de email (email vira opcional)

Revision ID: d4b04c7b9a0f
Revises: 6ecffe119883
Create Date: 2026-10-05 16:14:23.781128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4b04c7b9a0f'
down_revision: Union[str, None] = '6ecffe119883'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # e-mail deixa de ser a chave de login -- vira só um contato opcional.
    op.drop_constraint("usuario_email_key", "usuario", type_="unique")
    op.alter_column("usuario", "email", existing_type=sa.String(length=255), nullable=True)
    op.create_index(
        "uq_usuario_email",
        "usuario",
        ["email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )

    # login passa a ser pelo nome -- único só entre quem está ativo, pra um
    # ex-funcionário desligado não travar o nome pra quem entrar depois.
    op.create_index(
        "uq_usuario_nome_ativo",
        "usuario",
        [sa.text("lower(nome)")],
        unique=True,
        postgresql_where=sa.text("ativo = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_usuario_nome_ativo", table_name="usuario")
    op.drop_index("uq_usuario_email", table_name="usuario")
    op.alter_column("usuario", "email", existing_type=sa.String(length=255), nullable=False)
    op.create_unique_constraint("usuario_email_key", "usuario", ["email"])
