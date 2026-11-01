"""Add planes table for CU04.

Revision ID: 001_add_planes_table
Revises:
Create Date: 2026-10-31

"""
from alembic import op
import sqlalchemy as sa


revision = '001_add_planes_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'planes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('precio', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('duracion_dias', sa.Integer(), nullable=False),
        sa.Column('limite_sucursales', sa.Integer(), nullable=False),
        sa.Column('limite_usuarios', sa.Integer(), nullable=False),
        sa.Column('permite_prueba_gratuita', sa.Boolean(), nullable=False),
        sa.Column('duracion_prueba_dias', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
        sa.UniqueConstraint('slug'),
    )


def downgrade() -> None:
    op.drop_table('planes')
