"""create movimientos_inventario table

Revision ID: a2ccb4acde90
Revises: 825cb85ee62d
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2ccb4acde90'
down_revision: Union[str, Sequence[str], None] = '825cb85ee62d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # No se crea el tipo por separado: al ser una tabla nueva, create_table ya
    # emite el CREATE TYPE una sola vez para esta columna (a diferencia de la
    # migración de estado_producto_proveedor, que agregaba una columna a una
    # tabla EXISTENTE y sí necesitaba crear el tipo antes, con checkfirst).
    tipo_enum = sa.Enum(
        'AJUSTE_POSITIVO', 'AJUSTE_NEGATIVO', name='tipo_movimiento_inventario'
    )
    op.create_table(
        'movimientos_inventario',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sucursal_id', sa.Integer(), nullable=False),
        sa.Column('producto_variante_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('tipo', tipo_enum, nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('motivo', sa.String(length=300), nullable=False),
        sa.Column('stock_anterior', sa.Integer(), nullable=False),
        sa.Column('stock_resultante', sa.Integer(), nullable=False),
        sa.Column('fecha_hora', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id']),
        sa.ForeignKeyConstraint(
            ['producto_variante_id'], ['producto_variantes.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('cantidad > 0', name='ck_movimiento_inventario_cantidad_positiva'),
        sa.CheckConstraint(
            'stock_anterior >= 0 AND stock_resultante >= 0',
            name='ck_movimiento_inventario_stock_no_negativo',
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('movimientos_inventario')
    sa.Enum(name='tipo_movimiento_inventario').drop(op.get_bind(), checkfirst=True)
