"""adiciona default de data em sessao_grupo

Revision ID: 99cafb879563
Revises: 80dca9cbded0
Create Date: 2026-09-10 23:54:33.304092

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99cafb879563'
down_revision: Union[str, None] = '80dca9cbded0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # autogenerate nao detecta mudanca de server_default por padrao -- escrito a mao.
    op.alter_column(
        "sessao_grupo",
        "data",
        server_default=sa.text("CURRENT_DATE"),
    )


def downgrade() -> None:
    op.alter_column("sessao_grupo", "data", server_default=None)
