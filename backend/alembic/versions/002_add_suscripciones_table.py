"""Add suscripciones table for CU04 - CU05.

Revision ID: 002_add_suscripciones_table
Revises: 001_add_planes_table
Create Date: 2026-10-31

"""
from alembic import op
import sqlalchemy as sa


revision = '002_add_suscripciones_table'
down_revision = '001_add_planes_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'suscripciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('fecha_inicio', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fecha_vencimiento', sa.DateTime(timezone=True), nullable=False),
        sa.Column('en_prueba', sa.Boolean(), nullable=False),
        sa.Column('fecha_fin_prueba', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['plan_id'], ['planes.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_suscripciones_empresa_id', 'suscripciones', ['empresa_id'])
    op.create_index('ix_suscripciones_plan_id', 'suscripciones', ['plan_id'])


def downgrade() -> None:
    op.drop_index('ix_suscripciones_plan_id', table_name='suscripciones')
    op.drop_index('ix_suscripciones_empresa_id', table_name='suscripciones')
    op.drop_table('suscripciones')
