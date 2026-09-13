"""remove tabelas de grupos (sessao_grupo, presenca) - recurso descontinuado

Revision ID: 76b6b68697f0
Revises: 5df0cbfeb6fe
Create Date: 2026-09-13 11:26:18.985800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76b6b68697f0'
down_revision: Union[str, None] = '5df0cbfeb6fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # A tela de Grupos não vai mais ser usada -- apaga o histórico de
    # presença junto (não dá pra manter "presenca" órfã sem "sessao_grupo").
    # `presenca` primeiro: ela referencia `sessao_grupo` por FK.
    op.drop_table('presenca')
    op.drop_table('sessao_grupo')


def downgrade() -> None:
    # ordem invertida da upgrade: 'sessao_grupo' antes, pois 'presenca'
    # depende dela por FK.
    op.create_table('sessao_grupo',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('tipo_tratamento_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('data', sa.DATE(), server_default=sa.text('CURRENT_DATE'), autoincrement=False, nullable=False),
    sa.Column('responsavel_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('observacao', sa.TEXT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['responsavel_id'], ['pessoa.id'], name='sessao_grupo_responsavel_id_fkey', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tipo_tratamento_id'], ['tipo_tratamento.id'], name='sessao_grupo_tipo_tratamento_id_fkey', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name='sessao_grupo_pkey')
    )
    op.create_table('presenca',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('sessao_grupo_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('pessoa_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['pessoa_id'], ['pessoa.id'], name='presenca_pessoa_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sessao_grupo_id'], ['sessao_grupo.id'], name='presenca_sessao_grupo_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='presenca_pkey'),
    sa.UniqueConstraint('sessao_grupo_id', 'pessoa_id', name='uq_presenca')
    )
    # nota: os dados que existiam nessas tabelas antes da upgrade não voltam
    # -- downgrade recria a estrutura, não o conteúdo.
