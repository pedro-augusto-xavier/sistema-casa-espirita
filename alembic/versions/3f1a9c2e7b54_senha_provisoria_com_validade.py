"""senha provisória com validade

- usuario.senha_provisoria_expira_em: até quando a senha provisória vale.
  Depois disso o login com ela é recusado e o admin precisa redefinir.
- Quem já está com senha provisória ganha 7 dias a partir deste upgrade, pra
  dar tempo de entrar (as senhas novas valem 72h).

Revision ID: 3f1a9c2e7b54
Revises: ebd88c105dcf
Create Date: 2026-11-06 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "3f1a9c2e7b54"
down_revision: Union[str, None] = "ebd88c105dcf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuario",
        sa.Column("senha_provisoria_expira_em", sa.DateTime(timezone=True)),
    )
    op.execute(
        "UPDATE usuario SET senha_provisoria_expira_em = now() + interval '7 days' "
        "WHERE senha_provisoria = true"
    )


def downgrade() -> None:
    op.drop_column("usuario", "senha_provisoria_expira_em")
