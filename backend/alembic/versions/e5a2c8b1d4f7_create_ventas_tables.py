"""create ventas tables

Revision ID: e5a2c8b1d4f7
Revises: d4e8f1a6c7b3
Create Date: 2026-09-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5a2c8b1d4f7'
down_revision: Union[str, Sequence[str], None] = 'd4e8f1a6c7b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    tipo_venta = sa.Enum('DIGITAL', name='tipo_venta')
    estado_venta = sa.Enum('PENDIENTE_PAGO', name='estado_venta')

    op.create_table(
        'ventas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo_venta', sa.String(length=20), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('sucursal_id', sa.Integer(), nullable=False),
        sa.Column('tipo', tipo_venta, nullable=False),
        sa.Column('estado', estado_venta, nullable=False),
        sa.Column('total', sa.Numeric(10, 2), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo_venta', name='uq_ventas_codigo_venta'),
    )
    op.create_table(
        'venta_detalles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('venta_id', sa.Integer(), nullable=False),
        sa.Column('producto_variante_id', sa.Integer(), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(10, 2), nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(['venta_id'], ['ventas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['producto_variante_id'], ['producto_variantes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('cantidad > 0', name='ck_venta_detalle_cantidad_positiva'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('venta_detalles')
    op.drop_table('ventas')
    sa.Enum(name='estado_venta').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='tipo_venta').drop(op.get_bind(), checkfirst=True)
