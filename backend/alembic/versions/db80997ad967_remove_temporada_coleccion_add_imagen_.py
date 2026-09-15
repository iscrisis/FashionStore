"""remove temporada/coleccion, add imagen_url on productos_proveedor

Revision ID: db80997ad967
Revises: 0ac23efd4f26
Create Date: 2026-09-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db80997ad967'
down_revision: Union[str, Sequence[str], None] = '0ac23efd4f26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'productos_proveedor', sa.Column('imagen_url', sa.String(length=500), nullable=True)
    )
    op.drop_constraint(
        'productos_proveedor_temporada_id_fkey', 'productos_proveedor', type_='foreignkey'
    )
    op.drop_constraint(
        'productos_proveedor_coleccion_id_fkey', 'productos_proveedor', type_='foreignkey'
    )
    op.drop_column('productos_proveedor', 'temporada_id')
    op.drop_column('productos_proveedor', 'coleccion_id')


def downgrade() -> None:
    """Downgrade schema.

    temporada_id/coleccion_id vuelven NULLABLE (no se conserva el valor
    original: se perdió al hacer upgrade) para no romper filas creadas
    después del upgrade, que nunca tuvieron esos datos.
    """
    op.add_column(
        'productos_proveedor', sa.Column('temporada_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'productos_proveedor', sa.Column('coleccion_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'productos_proveedor_temporada_id_fkey',
        'productos_proveedor',
        'temporadas',
        ['temporada_id'],
        ['id'],
    )
    op.create_foreign_key(
        'productos_proveedor_coleccion_id_fkey',
        'productos_proveedor',
        'colecciones',
        ['coleccion_id'],
        ['id'],
    )
    op.drop_column('productos_proveedor', 'imagen_url')
