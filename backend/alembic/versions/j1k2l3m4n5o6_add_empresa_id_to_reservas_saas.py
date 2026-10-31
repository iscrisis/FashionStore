"""add empresa_id to reservas (SaaS multitenant)

Revision ID: j1k2l3m4n5o6
Revises: i0j1k2l3m4n5
Create Date: 2026-10-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j1k2l3m4n5o6'
down_revision: Union[str, Sequence[str], None] = 'b8d3c5f2e1a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add empresa_id for SaaS multitenant isolation."""
    # 1. Add empresa_id column (nullable initially)
    op.add_column('reservas', sa.Column('empresa_id', sa.Integer(), nullable=True))

    # 2. Populate empresa_id from sucursal relationship for existing records
    #    All existing reservas have sucursal_id, and all sucursales have empresa_id
    op.execute("""
        UPDATE reservas r
        SET empresa_id = s.empresa_id
        FROM sucursales s
        WHERE r.sucursal_id = s.id
    """)

    # 3. Make empresa_id NOT NULL now that all rows are populated
    op.alter_column('reservas', 'empresa_id', existing_type=sa.Integer(), nullable=False)

    # 4. Add FK constraint to empresas table for multitenant isolation
    op.create_foreign_key(
        'fk_reservas_empresa_id', 'reservas', 'empresas', ['empresa_id'], ['id']
    )

    # 5. Add composite FK to ensure reserva.empresa_id matches sucursal.empresa_id
    op.drop_constraint('reservas_sucursal_id_fkey1', 'reservas', type_='foreignkey')
    op.create_foreign_key(
        'fk_reserva_sucursal_compuesto', 'reservas', 'sucursales',
        ['empresa_id', 'sucursal_id'], ['empresa_id', 'id']
    )


def downgrade() -> None:
    """Downgrade schema - remove empresa_id from reservas."""
    # Drop composite FK to sucursales
    op.drop_constraint('fk_reserva_sucursal_compuesto', 'reservas', type_='foreignkey')

    # Restore simple FK to sucursales
    op.create_foreign_key(
        'reservas_sucursal_id_fkey1', 'reservas', 'sucursales', ['sucursal_id'], ['id']
    )

    # Drop FK to empresas
    op.drop_constraint('fk_reservas_empresa_id', 'reservas', type_='foreignkey')

    # Drop column
    op.drop_column('reservas', 'empresa_id')
