"""add empresa_id to usuarios table

Revision ID: f4d5e6a7b8c9
Revises: e5d4c3b2a1f0
Create Date: 2026-10-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4d5e6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'e5d4c3b2a1f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Agrega empresa_id a usuarios como NULLABLE para soportar SUPERADMIN
    (rol de plataforma global). La validación de negocio (SUPERADMIN → NULL,
    demás roles → obligatorio) ocurre en la capa de servicio.
    """
    # Verificar si la columna ya existe antes de agregarla
    # (en caso de que haya sido creada manualmente en desarrollo)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('usuarios')]

    if 'empresa_id' not in columns:
        # Agregar columna como nullable primero
        op.add_column('usuarios', sa.Column('empresa_id', sa.Integer(), nullable=True))
        # Agregar FK a empresas
        op.create_foreign_key('fk_usuarios_empresa_id', 'usuarios', 'empresas', ['empresa_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('usuarios')]

    if 'empresa_id' in columns:
        # Eliminar FK primero
        op.drop_constraint('fk_usuarios_empresa_id', 'usuarios', type_='foreignkey')
        # Luego eliminar columna
        op.drop_column('usuarios', 'empresa_id')
