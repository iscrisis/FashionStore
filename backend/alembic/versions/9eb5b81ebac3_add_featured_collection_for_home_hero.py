"""add featured collection for home hero

Revision ID: 9eb5b81ebac3
Revises: 5b8dfdb3e865
Create Date: 2026-09-10 21:16:37.374102

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9eb5b81ebac3'
down_revision: Union[str, Sequence[str], None] = '5b8dfdb3e865'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'colecciones',
        sa.Column('es_destacada_inicio', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column('colecciones', sa.Column('imagen_destacada_url', sa.String(length=500), nullable=True))
    # Garantiza a nivel de base de datos que a lo sumo una colección esté
    # marcada como destacada -- el índice solo cubre las filas en True, así
    # que las demás (False) no compiten por unicidad entre sí.
    op.create_index(
        'ix_colecciones_una_destacada_inicio',
        'colecciones',
        ['es_destacada_inicio'],
        unique=True,
        postgresql_where=sa.text('es_destacada_inicio'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_colecciones_una_destacada_inicio', table_name='colecciones')
    op.drop_column('colecciones', 'imagen_destacada_url')
    op.drop_column('colecciones', 'es_destacada_inicio')
