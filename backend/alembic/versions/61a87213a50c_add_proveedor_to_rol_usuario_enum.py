"""add proveedor to rol_usuario enum

Revision ID: 61a87213a50c
Revises: b3ce5bc51b48
Create Date: 2026-09-05 16:02:03.386732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61a87213a50c'
down_revision: Union[str, Sequence[str], None] = 'b3ce5bc51b48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ALTER TYPE ... ADD VALUE no puede ejecutarse dentro del bloque transaccional
    # normal de Alembic en PostgreSQL; autocommit_block() lo aísla en su propia
    # transacción, tal como documenta Alembic para este caso.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE rol_usuario ADD VALUE IF NOT EXISTS 'PROVEEDOR'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL no permite quitar un valor de un enum sin recrear el tipo
    # (y todas las columnas/constraints que dependen de él). No se implementa
    # para no arriesgar la tabla usuarios ya poblada; ver los otros valores de
    # rol_usuario, que tampoco tienen downgrade de este tipo.
    raise NotImplementedError(
        "No se puede revertir la adición de 'PROVEEDOR' a rol_usuario sin recrear el tipo enum."
    )
