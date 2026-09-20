"""create promociones tables (cu32)

Revision ID: e1a4c7f2b6d9
Revises: c8d4a1f6e930
Create Date: 2026-09-20 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1a4c7f2b6d9'
down_revision: Union[str, Sequence[str], None] = 'c8d4a1f6e930'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Tablas propias de CU32 -- una promoción PORCENTUAL (nunca cupones, 2x1
    # ni descuento fijo, ver Models/promocion.py) sobre uno o varios
    # Producto. Sin columna `estado`: se deriva en FastAPI a partir de
    # `activa` + fechas, nunca se guarda (ver
    # CU32_GestionarPromociones/service.py).
    op.create_table(
        'promociones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=150), nullable=False),
        sa.Column('porcentaje_descuento', sa.Numeric(5, 2), nullable=False),
        sa.Column('fecha_inicio', sa.Date(), nullable=False),
        sa.Column('fecha_fin', sa.Date(), nullable=False),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            'porcentaje_descuento > 0 AND porcentaje_descuento < 100',
            name='ck_promocion_porcentaje_rango',
        ),
        sa.CheckConstraint('fecha_fin >= fecha_inicio', name='ck_promocion_fechas_orden'),
    )

    # Asociación pura Promocion <-> Producto (sin datos propios) -- mismo
    # patrón ya usado por producto_tallas/producto_colores (CU08, P1).
    # producto_id SIN ondelete: CU08 nunca elimina físicamente un Producto,
    # solo lo desactiva.
    op.create_table(
        'promocion_productos',
        sa.Column('promocion_id', sa.Integer(), nullable=False),
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['promocion_id'], ['promociones.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id']),
        sa.PrimaryKeyConstraint('promocion_id', 'producto_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('promocion_productos')
    op.drop_table('promociones')
