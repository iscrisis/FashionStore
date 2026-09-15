"""create stock_sucursal table

Revision ID: a7c142f6d9b3
Revises: f6396ef38f16
Create Date: 2026-09-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c142f6d9b3'
down_revision: Union[str, Sequence[str], None] = 'f6396ef38f16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'stock_sucursal',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sucursal_id', sa.Integer(), nullable=False),
        sa.Column('producto_variante_id', sa.Integer(), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id']),
        sa.ForeignKeyConstraint(
            ['producto_variante_id'], ['producto_variantes.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sucursal_id', 'producto_variante_id'),
        sa.CheckConstraint('cantidad >= 0', name='ck_stock_sucursal_cantidad_no_negativa'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('stock_sucursal')
