"""create empresas table

Revision ID: e5d4c3b2a1f0
Revises: 01fc433635a1
Create Date: 2026-10-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5d4c3b2a1f0'
down_revision: Union[str, Sequence[str], None] = 'a7f21c4d9b3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Crea tabla empresas como raíz del tenant en arquitectura multitenant.
    Esta tabla debería haberse creado en migraciones anteriores pero fue omitida.
    Se crea aquí como corrección retroactiva.
    """
    # Verificar si la tabla ya existe
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()

    if 'empresas' not in tables:
        op.create_table('empresas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('razon_social', sa.String(length=200), nullable=False),
        sa.Column('correo', sa.String(length=255), nullable=False),
        sa.Column('telefono', sa.String(length=30), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_unique_constraint('uq_empresa_nombre', 'empresas', ['nombre'])
        op.create_unique_constraint('uq_empresa_slug', 'empresas', ['slug'])


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()

    if 'empresas' in tables:
        op.drop_constraint('uq_empresa_slug', 'empresas', type_='unique')
        op.drop_constraint('uq_empresa_nombre', 'empresas', type_='unique')
        op.drop_table('empresas')
