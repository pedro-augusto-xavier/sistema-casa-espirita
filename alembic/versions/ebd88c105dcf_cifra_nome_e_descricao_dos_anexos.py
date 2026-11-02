"""cifra o nome e a descrição dos anexos

O arquivo já era cifrado, mas o nome ("exame_fulana.pdf") e a descrição
("laudo do psiquiatra") ficavam legíveis no banco. Agora seguem o mesmo
AES-256-GCM, com a chave de CHAVES_CRIPTOGRAFIA.

Reversível: o downgrade decifra de volta pros tipos originais
(varchar(255) e text), com as mesmas chaves.

Revision ID: ebd88c105dcf
Revises: 0dc7d794e5e5
Create Date: 2026-11-02 21:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.cripto import cifrar, decifrar

revision: str = "ebd88c105dcf"
down_revision: Union[str, None] = "0dc7d794e5e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (coluna, contexto da criptografia, tipo original, aceita nulo)
COLUNAS = [
    ("nome_arquivo", "anexo.nome_arquivo", sa.String(length=255), False),
    ("descricao", "anexo.descricao", sa.Text(), True),
]


def _troca_coluna(coluna, tipo_novo, converter, nula) -> None:
    """Coluna temporária, converte linha a linha, troca pela original."""
    conn = op.get_bind()
    temporaria = f"{coluna}_tmp_cripto"
    op.add_column("anexo", sa.Column(temporaria, tipo_novo))
    linhas = conn.execute(
        sa.text(f"SELECT id, {coluna} FROM anexo WHERE {coluna} IS NOT NULL")
    ).all()
    for id_, valor in linhas:
        conn.execute(
            sa.text(f"UPDATE anexo SET {temporaria} = :valor WHERE id = :id"),
            {"valor": converter(valor), "id": id_},
        )
    op.drop_column("anexo", coluna)
    op.alter_column("anexo", temporaria, new_column_name=coluna, nullable=nula)


def upgrade() -> None:
    for coluna, contexto, _tipo, nula in COLUNAS:
        _troca_coluna(
            coluna,
            sa.LargeBinary(),
            lambda valor, ctx=contexto: cifrar(valor.encode("utf-8"), ctx),
            nula,
        )


def downgrade() -> None:
    for coluna, contexto, tipo, nula in COLUNAS:
        _troca_coluna(
            coluna,
            tipo,
            lambda valor, ctx=contexto: decifrar(bytes(valor), ctx).decode("utf-8"),
            nula,
        )
