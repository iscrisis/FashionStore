"""create recepcion mercaderia tables

Revision ID: 0ac23efd4f26
Revises: a7c142f6d9b3
Create Date: 2026-09-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ac23efd4f26'
down_revision: Union[str, Sequence[str], None] = 'a7c142f6d9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'recepciones_mercaderia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('proveedor_id', sa.Integer(), nullable=False),
        sa.Column('sucursal_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('fecha_hora', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('observacion', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['proveedor_id'], ['proveedores.id']),
        sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id']),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'detalles_recepcion_mercaderia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recepcion_id', sa.Integer(), nullable=False),
        sa.Column('producto_variante_id', sa.Integer(), nullable=False),
        sa.Column('cantidad_recibida', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['recepcion_id'], ['recepciones_mercaderia.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['producto_variante_id'], ['producto_variantes.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('cantidad_recibida > 0', name='ck_detalle_recepcion_cantidad_positiva'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('detalles_recepcion_mercaderia')
    op.drop_table('recepciones_mercaderia')
