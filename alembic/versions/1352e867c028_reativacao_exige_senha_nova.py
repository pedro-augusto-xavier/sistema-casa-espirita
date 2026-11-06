"""reativação exige senha nova

O backfill de 0adbab7209a9 só marcou senha provisória em quem estava ativo.
Conta que estava desativada ficou com a senha antiga (de antes das regras de
core/senhas.py) e, ao ser reativada, entrava com ela sem ter que trocar.

Aqui toda conta que nunca passou pelas regras novas (senha_provisoria = false
e senha_alterada_em IS NULL) vira senha provisória já vencida: a senha antiga
não serve mais, e só o admin reativando ou redefinindo libera de novo (com
senha gerada pelo servidor).

Revision ID: 1352e867c028
Revises: 3f1a9c2e7b54
Create Date: 2026-11-06 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "1352e867c028"
down_revision: Union[str, None] = "3f1a9c2e7b54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE usuario SET senha_provisoria = true, "
        "senha_provisoria_expira_em = now() "
        "WHERE senha_provisoria = false AND senha_alterada_em IS NULL"
    )


def downgrade() -> None:
    # De propósito não desfaz: voltar o flag reabriria a falha, e não dá pra
    # saber quais linhas este upgrade mudou.
    pass
