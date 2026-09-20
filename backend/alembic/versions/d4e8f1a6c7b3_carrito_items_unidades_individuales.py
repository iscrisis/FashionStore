"""carrito_items: unidades individuales en vez de cantidad

Corrección de CU21: cada fila de carrito_items ahora representa UNA unidad
concreta de una variante (Producto + Color + Talla), no una línea con
cantidad. Agregar la misma variante otra vez crea una segunda fila
independiente -- por eso se elimina la UniqueConstraint por
(carrito_id, producto_variante_id) y la columna `cantidad`. Se agrega
`seleccionado` para marcar, por unidad, cuáles prendas se consideran para
una compra futura (no crea Venta ni Pago).

Revision ID: d4e8f1a6c7b3
Revises: b1f4c7a9e3d2
Create Date: 2026-09-18 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e8f1a6c7b3'
down_revision: Union[str, Sequence[str], None] = 'b1f4c7a9e3d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('uq_carrito_items_carrito_variante', 'carrito_items', type_='unique')
    op.drop_constraint('ck_carrito_items_cantidad_valida', 'carrito_items', type_='check')
    op.drop_column('carrito_items', 'cantidad')
    op.add_column(
        'carrito_items',
        sa.Column('seleccionado', sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('carrito_items', 'seleccionado')
    op.add_column('carrito_items', sa.Column('cantidad', sa.Integer(), nullable=False, server_default='1'))
    op.create_check_constraint('ck_carrito_items_cantidad_valida', 'carrito_items', 'cantidad >= 1')
    op.create_unique_constraint(
        'uq_carrito_items_carrito_variante', 'carrito_items', ['carrito_id', 'producto_variante_id']
    )
