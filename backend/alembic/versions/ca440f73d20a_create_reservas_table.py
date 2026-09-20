"""create reservas table

Revision ID: ca440f73d20a
Revises: a2ccb4acde90
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca440f73d20a'
down_revision: Union[str, Sequence[str], None] = 'a2ccb4acde90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    estado_enum = sa.Enum('PENDIENTE', 'CANCELADA', 'ATENDIDA', name='estado_reserva')
    op.create_table(
        'reservas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('sucursal_id', sa.Integer(), nullable=False),
        sa.Column('producto_variante_id', sa.Integer(), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('estado', estado_enum, nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id']),
        sa.ForeignKeyConstraint(
            ['producto_variante_id'], ['producto_variantes.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('cantidad > 0', name='ck_reserva_cantidad_positiva'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('reservas')
    sa.Enum(name='estado_reserva').drop(op.get_bind(), checkfirst=True)
