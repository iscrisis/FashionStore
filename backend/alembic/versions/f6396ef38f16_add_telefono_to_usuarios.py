"""add telefono to usuarios

Revision ID: f6396ef38f16
Revises: e4429f358af5
Create Date: 2026-09-12 00:10:53.668596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6396ef38f16'
down_revision: Union[str, Sequence[str], None] = 'e4429f358af5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # NOTA: el autogenerate también detectó un drop de 'stock_sucursal' y de
    # 'ix_colecciones_una_destacada_inicio' -- drift de otras ramas (GestionStockSucursal,
    # CU10) contra esta misma base de datos compartida, ajeno a esta corrección. Se omite
    # deliberadamente para no borrar esa tabla/índice desde esta migración.
    op.add_column('usuarios', sa.Column('telefono', sa.String(length=30), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('usuarios', 'telefono')
