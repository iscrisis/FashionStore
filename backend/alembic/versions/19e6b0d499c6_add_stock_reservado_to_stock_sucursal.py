"""add stock_reservado to stock_sucursal

Revision ID: 19e6b0d499c6
Revises: 39020e8b11cc
Create Date: 2026-09-16 15:08:31.736881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19e6b0d499c6'
down_revision: Union[str, Sequence[str], None] = '39020e8b11cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default='0' rellena las filas existentes (stock ya cargado por
    # CU14/CU15/CU16 antes de que existiera CU17) sin dejarlas en NULL -- sin
    # reservas previas, stock_reservado real de esas filas es 0.
    op.add_column(
        'stock_sucursal',
        sa.Column('stock_reservado', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_check_constraint(
        'ck_stock_sucursal_reservado_no_negativo', 'stock_sucursal', 'stock_reservado >= 0'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_stock_sucursal_reservado_no_negativo', 'stock_sucursal', type_='check')
    op.drop_column('stock_sucursal', 'stock_reservado')
