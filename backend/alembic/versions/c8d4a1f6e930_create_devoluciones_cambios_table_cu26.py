"""create devoluciones_cambios table (cu26)

Revision ID: c8d4a1f6e930
Revises: d2b8e5f19a4c
Create Date: 2026-09-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c8d4a1f6e930'
down_revision: Union[str, Sequence[str], None] = 'd2b8e5f19a4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Tabla propia de CU26 -- trazabilidad de devoluciones/cambios sobre una
    # línea (venta_detalle) de una Venta ya PAGADA. `proveedor_pago` ya
    # existe (CU23/CU25) y se reutiliza tal cual para `metodo_reembolso` --
    # el reembolso siempre usa el mismo método con el que se pagó. Los tres
    # enums nuevos NO se crean con un `.create()` separado -- se declaran
    # aquí y `create_table` los crea una sola vez (mismo patrón ya usado en
    # f3c9d6e2a815_create_pagos_table_cu23.py para `proveedor_pago`/
    # `estado_pago`); crearlos antes Y dejarlos embebidos en las columnas
    # duplica el `CREATE TYPE` y revienta con "already exists".
    tipo_operacion_devolucion = sa.Enum('DEVOLUCION', 'CAMBIO', name='tipo_operacion_devolucion')
    motivo_devolucion = sa.Enum('TALLA', 'DEFECTO', 'PRODUCTO_INCORRECTO', 'OTRO', name='motivo_devolucion')
    estado_reembolso = sa.Enum('REGISTRADO', 'COMPLETADO', name='estado_reembolso')

    op.create_table(
        'devoluciones_cambios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('venta_id', sa.Integer(), nullable=False),
        sa.Column('venta_detalle_id', sa.Integer(), nullable=False),
        sa.Column('tipo', tipo_operacion_devolucion, nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('variante_original_id', sa.Integer(), nullable=False),
        sa.Column('variante_nueva_id', sa.Integer(), nullable=True),
        sa.Column('motivo', motivo_devolucion, nullable=True),
        sa.Column('observacion', sa.String(length=300), nullable=True),
        sa.Column('monto_reembolso', sa.Numeric(10, 2), nullable=True),
        sa.Column(
            'metodo_reembolso',
            postgresql.ENUM('STRIPE', 'EFECTIVO', 'TARJETA', 'QR', name='proveedor_pago', create_type=False),
            nullable=True,
        ),
        sa.Column('estado_reembolso', estado_reembolso, nullable=True),
        sa.Column('stripe_refund_id', sa.String(length=255), nullable=True),
        sa.Column('cajero_id', sa.Integer(), nullable=False),
        sa.Column('sucursal_id', sa.Integer(), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['venta_id'], ['ventas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['venta_detalle_id'], ['venta_detalles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variante_original_id'], ['producto_variantes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variante_nueva_id'], ['producto_variantes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cajero_id'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('cantidad > 0', name='ck_devolucion_cambio_cantidad_positiva'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('devoluciones_cambios')
    sa.Enum(name='estado_reembolso').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='motivo_devolucion').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='tipo_operacion_devolucion').drop(op.get_bind(), checkfirst=True)
