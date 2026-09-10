"""adiciona pessoa.anonimizada

Revision ID: 80dca9cbded0
Revises: 34042df99899
Create Date: 2026-09-10 18:32:04.165634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80dca9cbded0'
down_revision: Union[str, None] = '34042df99899'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default garante que linhas já existentes recebam FALSE.
    op.add_column(
        "pessoa",
        sa.Column(
            "anonimizada",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    # a partir daqui o default fica por conta da aplicação
    op.alter_column("pessoa", "anonimizada", server_default=None)


def downgrade() -> None:
    op.drop_column("pessoa", "anonimizada")
