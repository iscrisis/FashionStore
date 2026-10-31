"""add empresa_id to promociones for SaaS

Revision ID: i0j1k2l3m4n5
Revises: c8d4a1f6e930
Create Date: 2026-10-28 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i0j1k2l3m4n5'
down_revision: Union[str, Sequence[str], None] = 'c8d4a1f6e930'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add empresa_id to promociones and promocion_productos."""
    # Add empresa_id to promociones
    op.add_column(
        'promociones',
        sa.Column('empresa_id', sa.Integer(), nullable=False, server_default='1')
    )
    op.create_foreign_key(
        'fk_promociones_empresa_id',
        'promociones',
        'empresas',
        ['empresa_id'],
        ['id']
    )

    # Add empresa_id to promocion_productos
    op.add_column(
        'promocion_productos',
        sa.Column('empresa_id', sa.Integer(), nullable=False, server_default='1')
    )
    op.create_foreign_key(
        'fk_promocion_productos_empresa_id',
        'promocion_productos',
        'empresas',
        ['empresa_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_promocion_productos_empresa_id', 'promocion_productos', type_='foreignkey')
    op.drop_column('promocion_productos', 'empresa_id')
    op.drop_constraint('fk_promociones_empresa_id', 'promociones', type_='foreignkey')
    op.drop_column('promociones', 'empresa_id')
