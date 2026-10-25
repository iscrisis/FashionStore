"""add empresa_id to ciudades and sucursales

Revision ID: g6h7i8j9k0l1
Revises: e1a4c7f2b6d9
Create Date: 2026-10-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g6h7i8j9k0l1'
down_revision: Union[str, Sequence[str], None] = 'e1a4c7f2b6d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar empresa_id a ciudades
    op.add_column('ciudades', sa.Column('empresa_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_ciudades_empresa_id', 'ciudades', 'empresas', ['empresa_id'], ['id'])

    # Agregar empresa_id a sucursales
    op.add_column('sucursales', sa.Column('empresa_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_sucursales_empresa_id', 'sucursales', 'empresas', ['empresa_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_sucursales_empresa_id', 'sucursales', type_='foreignkey')
    op.drop_column('sucursales', 'empresa_id')

    op.drop_constraint('fk_ciudades_empresa_id', 'ciudades', type_='foreignkey')
    op.drop_column('ciudades', 'empresa_id')
