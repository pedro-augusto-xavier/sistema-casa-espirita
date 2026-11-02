"""criptografa CPF, observações, diário e anexos (AES-256-GCM)

Cifra o que já está no banco com a chave de CHAVES_CRIPTOGRAFIA -- por
isso as variáveis CHAVES_CRIPTOGRAFIA e CHAVE_HMAC precisam estar
configuradas ANTES desta migration rodar (no Render: Environment).

- pessoa.cpf (texto) -> pessoa.cpf_cifrado (bytes) + pessoa.cpf_hash
  (HMAC, pra conferir duplicado e buscar pelo CPF completo).
- observações / situação final / diário: mesma coluna, agora bytes cifrados.
- anexo.conteudo: os bytes do arquivo passam a ficar cifrados.

O downgrade decifra tudo de volta (com as mesmas chaves).

Revision ID: 7335d561821b
Revises: 0adbab7209a9
Create Date: 2026-11-02 19:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.cripto import cifrar, decifrar, hmac_busca

revision: str = "7335d561821b"
down_revision: Union[str, None] = "0adbab7209a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (tabela, coluna, contexto da criptografia, aceita nulo)
COLUNAS_DE_TEXTO = [
    ("pessoa", "observacoes_gerais", "pessoa.observacoes_gerais", True),
    ("atendimento", "observacao", "atendimento.observacao", True),
    ("atendimento_tratamento", "observacao", "atendimento_tratamento.observacao", True),
    ("tratamento", "situacao_final", "tratamento.situacao_final", True),
    ("tratamento", "observacao", "tratamento.observacao", True),
    (
        "tratamento_assistido",
        "situacao_final",
        "tratamento_assistido.situacao_final",
        True,
    ),
    ("tratamento_evolucao", "texto", "tratamento_evolucao.texto", False),
]


def _troca_coluna(tabela, coluna, tipo_novo, converter, nula) -> None:
    """Cria uma coluna temporária, converte linha a linha, apaga a antiga e
    renomeia a nova pro nome original."""
    conn = op.get_bind()
    temporaria = f"{coluna}_tmp_cripto"
    op.add_column(tabela, sa.Column(temporaria, tipo_novo))
    linhas = conn.execute(
        sa.text(f"SELECT id, {coluna} FROM {tabela} WHERE {coluna} IS NOT NULL")
    ).all()
    for id_, valor in linhas:
        conn.execute(
            sa.text(f"UPDATE {tabela} SET {temporaria} = :valor WHERE id = :id"),
            {"valor": converter(valor), "id": id_},
        )
    op.drop_column(tabela, coluna)
    op.alter_column(tabela, temporaria, new_column_name=coluna, nullable=nula)


def _reescreve_anexos(converter) -> None:
    """Um arquivo por vez -- podem ser vários MB cada."""
    conn = op.get_bind()
    ids = conn.execute(sa.text("SELECT id FROM anexo ORDER BY id")).scalars().all()
    for id_ in ids:
        conteudo = conn.execute(
            sa.text("SELECT conteudo FROM anexo WHERE id = :id"), {"id": id_}
        ).scalar_one()
        conn.execute(
            sa.text("UPDATE anexo SET conteudo = :c WHERE id = :id"),
            {"c": converter(bytes(conteudo)), "id": id_},
        )


def upgrade() -> None:
    conn = op.get_bind()

    # --- CPF ---
    op.add_column("pessoa", sa.Column("cpf_cifrado", sa.LargeBinary()))
    op.add_column("pessoa", sa.Column("cpf_hash", sa.String(length=64)))
    for id_, cpf in conn.execute(
        sa.text("SELECT id, cpf FROM pessoa WHERE cpf IS NOT NULL")
    ).all():
        conn.execute(
            sa.text(
                "UPDATE pessoa SET cpf_cifrado = :cifrado, cpf_hash = :hash WHERE id = :id"
            ),
            {
                "cifrado": cifrar(cpf.encode("utf-8"), "pessoa.cpf"),
                "hash": hmac_busca(cpf),
                "id": id_,
            },
        )
    op.drop_index(
        "uq_pessoa_cpf", table_name="pessoa", postgresql_where=sa.text("cpf IS NOT NULL")
    )
    op.drop_column("pessoa", "cpf")
    op.create_index(
        "uq_pessoa_cpf_hash",
        "pessoa",
        ["cpf_hash"],
        unique=True,
        postgresql_where=sa.text("cpf_hash IS NOT NULL"),
    )

    # --- textos livres ---
    for tabela, coluna, contexto, nula in COLUNAS_DE_TEXTO:
        _troca_coluna(
            tabela,
            coluna,
            sa.LargeBinary(),
            lambda valor, ctx=contexto: cifrar(valor.encode("utf-8"), ctx),
            nula,
        )

    # --- anexos ---
    _reescreve_anexos(lambda dados: cifrar(dados, "anexo.conteudo"))


def downgrade() -> None:
    conn = op.get_bind()

    _reescreve_anexos(lambda dados: decifrar(dados, "anexo.conteudo"))

    for tabela, coluna, contexto, nula in COLUNAS_DE_TEXTO:
        _troca_coluna(
            tabela,
            coluna,
            sa.Text(),
            lambda valor, ctx=contexto: decifrar(bytes(valor), ctx).decode("utf-8"),
            nula,
        )

    op.drop_index(
        "uq_pessoa_cpf_hash",
        table_name="pessoa",
        postgresql_where=sa.text("cpf_hash IS NOT NULL"),
    )
    op.add_column("pessoa", sa.Column("cpf", sa.String(length=11)))
    for id_, cifrado in conn.execute(
        sa.text("SELECT id, cpf_cifrado FROM pessoa WHERE cpf_cifrado IS NOT NULL")
    ).all():
        conn.execute(
            sa.text("UPDATE pessoa SET cpf = :cpf WHERE id = :id"),
            {"cpf": decifrar(bytes(cifrado), "pessoa.cpf").decode("utf-8"), "id": id_},
        )
    op.drop_column("pessoa", "cpf_hash")
    op.drop_column("pessoa", "cpf_cifrado")
    op.create_index(
        "uq_pessoa_cpf",
        "pessoa",
        ["cpf"],
        unique=True,
        postgresql_where=sa.text("cpf IS NOT NULL"),
    )
