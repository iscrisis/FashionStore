"""add empresa_id to ventas (SaaS multitenant)

Revision ID: b8d3c5f2e1a6
Revises: d2b8e5f19a4c, i0j1k2l3m4n5
Create Date: 2026-10-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8d3c5f2e1a6'
down_revision: Union[str, Sequence[str], None] = ('d2b8e5f19a4c', 'i0j1k2l3m4n5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add empresa_id for SaaS multitenant isolation."""
    # 1. Add empresa_id column (nullable initially)
    op.add_column('ventas', sa.Column('empresa_id', sa.Integer(), nullable=True))

    # 2. Populate empresa_id from sucursal relationship for existing records
    #    All existing ventas have sucursal_id, and all sucursales have empresa_id
    op.execute("""
        UPDATE ventas v
        SET empresa_id = s.empresa_id
        FROM sucursales s
        WHERE v.sucursal_id = s.id
    """)

    # 3. Make empresa_id NOT NULL now that all rows are populated
    op.alter_column('ventas', 'empresa_id', existing_type=sa.Integer(), nullable=False)

    # 4. Add FK constraint to empresas table for multitenant isolation
    op.create_foreign_key(
        'fk_ventas_empresa_id', 'ventas', 'empresas', ['empresa_id'], ['id']
    )


def downgrade() -> None:
    """Downgrade schema - remove empresa_id from ventas."""
    # Drop FK to empresas
    op.drop_constraint('fk_ventas_empresa_id', 'ventas', type_='foreignkey')

    # Drop column
    op.drop_column('ventas', 'empresa_id')
