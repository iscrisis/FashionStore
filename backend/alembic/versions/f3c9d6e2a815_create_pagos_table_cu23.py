"""create pagos table and extend venta for cu23

Revision ID: f3c9d6e2a815
Revises: e5a2c8b1d4f7
Create Date: 2026-09-19 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3c9d6e2a815'
down_revision: Union[str, Sequence[str], None] = 'e5a2c8b1d4f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. CU23 agrega PAGADA a estado_venta -- mismo patrón ya usado para
    #    ampliar estado_reserva en CU20 (ALTER TYPE ADD VALUE, sin recrear
    #    el tipo ni tocar ninguna fila existente).
    op.execute("ALTER TYPE estado_venta ADD VALUE IF NOT EXISTS 'PAGADA'")

    # 2. venta_detalles.carrito_item_id -- referencia al CarritoItem del que
    #    salió esa línea, para que CU23 sepa exactamente qué filas del
    #    carrito borrar al confirmar el pago (ver Models/venta.py).
    op.add_column(
        'venta_detalles',
        sa.Column('carrito_item_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_venta_detalles_carrito_item_id',
        'venta_detalles',
        'carrito_items',
        ['carrito_item_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # 3. Tabla propia de CU23: Pago (trazabilidad de cada intento de cobro).
    proveedor_pago = sa.Enum('STRIPE', name='proveedor_pago')
    estado_pago = sa.Enum('PENDIENTE', 'PAGADO', 'CANCELADO', 'FALLIDO', name='estado_pago')

    op.create_table(
        'pagos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('venta_id', sa.Integer(), nullable=False),
        sa.Column('proveedor', proveedor_pago, nullable=False),
        sa.Column('stripe_checkout_session_id', sa.String(length=255), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True),
        sa.Column('monto', sa.Numeric(10, 2), nullable=False),
        sa.Column('estado', estado_pago, nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('fecha_confirmacion', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['venta_id'], ['ventas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_checkout_session_id', name='uq_pagos_stripe_checkout_session_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('pagos')
    sa.Enum(name='estado_pago').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='proveedor_pago').drop(op.get_bind(), checkfirst=True)

    op.drop_constraint('fk_venta_detalles_carrito_item_id', 'venta_detalles', type_='foreignkey')
    op.drop_column('venta_detalles', 'carrito_item_id')

    # PostgreSQL no permite quitar un valor de un enum sin recrear el tipo
    # completo -- mismo criterio ya usado al ampliar estado_reserva (CU20):
    # se deja como no-op a propósito, bajar esta revisión no arriesga datos.
