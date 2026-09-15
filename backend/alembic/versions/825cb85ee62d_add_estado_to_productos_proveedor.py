"""add estado to productos_proveedor

Revision ID: 825cb85ee62d
Revises: db80997ad967
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '825cb85ee62d'
down_revision: Union[str, Sequence[str], None] = 'db80997ad967'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    estado_enum = sa.Enum(
        'PENDIENTE', 'APROBADO', 'RECHAZADO', name='estado_producto_proveedor'
    )
    estado_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'productos_proveedor',
        sa.Column('estado', estado_enum, nullable=False, server_default='PENDIENTE'),
    )

    # Compatibilidad con datos existentes: una propuesta que ya tiene un
    # Producto (CU08) vinculado quedó APROBADA aunque se haya convertido
    # antes de que existiera esta columna. El resto sigue PENDIENTE por el
    # server_default de arriba -- ninguna propuesta se pierde ni se marca
    # RECHAZADA de forma retroactiva (eso solo lo decide un Administrador).
    op.execute(
        """
        UPDATE productos_proveedor
        SET estado = 'APROBADO'
        WHERE id IN (
            SELECT producto_proveedor_id FROM productos
            WHERE producto_proveedor_id IS NOT NULL
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('productos_proveedor', 'estado')
    sa.Enum(name='estado_producto_proveedor').drop(op.get_bind(), checkfirst=True)
