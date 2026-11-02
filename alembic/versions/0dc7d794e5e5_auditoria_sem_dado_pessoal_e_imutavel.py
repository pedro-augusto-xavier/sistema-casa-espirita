"""auditoria sem cópia de dado pessoal, e só de inserção (imutável)

1. Limpa os registros antigos: até aqui, editar uma ficha guardava no log
   o valor antigo e o novo de cada campo (CPF, endereço, observações...).
   Isso deixava uma cópia dos dados fora da criptografia e que sobrevivia
   à anonimização. Agora fica só a informação de QUE o campo mudou.
2. Trigger no banco: UPDATE, DELETE e TRUNCATE em audit_log são recusados.
   Quem invadir o app não consegue apagar o rastro (com o usuário de banco
   restrito -- ver docs/SEGURANCA.md -- nem desligar o trigger).

O downgrade só remove o trigger; os valores apagados no passo 1 não voltam.

Revision ID: 0dc7d794e5e5
Revises: 7335d561821b
Create Date: 2026-11-02 19:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0dc7d794e5e5"
down_revision: Union[str, None] = "7335d561821b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Campos de pessoa cujo valor não pode ficar no log.
CAMPOS_PESSOAIS = {
    "nome_completo",
    "cpf",
    "telefone",
    "data_nascimento",
    "sexo",
    "estado_civil",
    "quantidade_filhos",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cidade",
    "uf",
    "cep",
    "como_conheceu",
    "observacoes_gerais",
}
# Textos livres (observação, diário...) em qualquer entidade.
TEXTOS_SENSIVEIS = {"observacao", "situacao_final", "texto", "descricao"}


def _limpa(entidade: str, dados: dict) -> dict:
    limpo = {}
    for chave, valor in dados.items():
        if chave == "nome_arquivo":
            continue  # às vezes é "rg_fulana.jpg"
        if (entidade == "pessoa" and chave in CAMPOS_PESSOAIS) or (
            chave in TEXTOS_SENSIVEIS
        ):
            limpo[chave] = {"alterado": True}
        else:
            limpo[chave] = valor
    return limpo


def upgrade() -> None:
    conn = op.get_bind()
    atualizar = sa.text("UPDATE audit_log SET dados = :dados WHERE id = :id").bindparams(
        sa.bindparam("dados", type_=JSONB)
    )
    for id_, entidade, dados in conn.execute(
        sa.text("SELECT id, entidade, dados FROM audit_log WHERE dados IS NOT NULL")
    ).all():
        if not isinstance(dados, dict):
            continue
        limpo = _limpa(entidade, dados)
        if limpo != dados:
            conn.execute(atualizar, {"dados": limpo, "id": id_})

    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_log_somente_insercao() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_log é só de inserção: registros de auditoria não podem ser alterados nem apagados';
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_imutavel
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_somente_insercao()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_sem_truncate
        BEFORE TRUNCATE ON audit_log
        FOR EACH STATEMENT EXECUTE FUNCTION audit_log_somente_insercao()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_sem_truncate ON audit_log")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_imutavel ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS audit_log_somente_insercao()")
