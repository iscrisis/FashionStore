"""Add uuid_operacion_offline to Venta and Reserva for CU12 synchronization.

Revision ID: k2l3m4n5o6p7
Revises: j1k2l3m4n5o6
Create Date: 2026-11-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k2l3m4n5o6p7'
down_revision = 'j1k2l3m4n5o6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add uuid_operacion_offline to ventas table
    op.add_column('ventas', sa.Column('uuid_operacion_offline', sa.String(255), nullable=True))
    op.create_unique_constraint('uq_ventas_uuid_operacion_offline', 'ventas', ['uuid_operacion_offline'])

    # Add uuid_operacion_offline to reservas table
    op.add_column('reservas', sa.Column('uuid_operacion_offline', sa.String(255), nullable=True))
    op.create_unique_constraint('uq_reservas_uuid_operacion_offline', 'reservas', ['uuid_operacion_offline'])


def downgrade() -> None:
    # Drop constraints and columns
    op.drop_constraint('uq_reservas_uuid_operacion_offline', 'reservas', type_='unique')
    op.drop_column('reservas', 'uuid_operacion_offline')

    op.drop_constraint('uq_ventas_uuid_operacion_offline', 'ventas', type_='unique')
    op.drop_column('ventas', 'uuid_operacion_offline')
