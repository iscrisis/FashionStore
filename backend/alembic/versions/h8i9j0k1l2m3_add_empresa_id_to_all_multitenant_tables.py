"""add empresa_id to all multitenant tables

Revision ID: h8i9j0k1l2m3
Revises: g6h7i8j9k0l1
Create Date: 2026-10-24 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h8i9j0k1l2m3'
down_revision: Union[str, Sequence[str], None] = 'g6h7i8j9k0l1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add empresa_id to all multitenant tables."""
    tables_to_add = [
        'proveedores',
        'tallas',
        'colores',
        'categorias',
        'temporadas',
        'colecciones',
        'productos'
    ]

    for table in tables_to_add:
        try:
            op.add_column(table, sa.Column('empresa_id', sa.Integer(), nullable=True))
            op.create_foreign_key(f'fk_{table}_empresa_id', table, 'empresas', ['empresa_id'], ['id'])
        except Exception:
            pass


def downgrade() -> None:
    """Downgrade schema."""
    tables_to_remove = [
        'productos',
        'colecciones',
        'temporadas',
        'categorias',
        'colores',
        'tallas',
        'proveedores'
    ]

    for table in tables_to_remove:
        try:
            op.drop_constraint(f'fk_{table}_empresa_id', table, type_='foreignkey')
            op.drop_column(table, 'empresa_id')
        except Exception:
            pass
