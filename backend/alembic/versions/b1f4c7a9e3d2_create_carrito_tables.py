"""create carrito tables

Revision ID: b1f4c7a9e3d2
Revises: 7a1c9e4f2b3d
Create Date: 2026-09-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1f4c7a9e3d2'
down_revision: Union[str, Sequence[str], None] = '7a1c9e4f2b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'carritos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('fecha_actualizacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cliente_id', name='uq_carritos_cliente_id'),
    )
    op.create_table(
        'carrito_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('carrito_id', sa.Integer(), nullable=False),
        sa.Column('producto_variante_id', sa.Integer(), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('fecha_agregado', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['carrito_id'], ['carritos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['producto_variante_id'], ['producto_variantes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'carrito_id', 'producto_variante_id', name='uq_carrito_items_carrito_variante'
        ),
        sa.CheckConstraint('cantidad >= 1', name='ck_carrito_items_cantidad_valida'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('carrito_items')
    op.drop_table('carritos')
