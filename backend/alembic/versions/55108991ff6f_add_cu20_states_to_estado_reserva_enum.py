"""add cu20 states to estado_reserva enum

Revision ID: 55108991ff6f
Revises: 19e6b0d499c6
Create Date: 2026-09-16 16:57:24.563017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55108991ff6f'
down_revision: Union[str, Sequence[str], None] = '19e6b0d499c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # PostgreSQL 12+ permite ADD VALUE dentro de una transacción siempre que
    # el valor nuevo no se USE en esa misma transacción (no es el caso: esta
    # migración solo amplía las etiquetas del enum, no escribe filas) -- ver
    # Models/reserva.py para el flujo completo que introduce CU20.
    for valor in ("PREPARADA", "EN_ATENCION", "LISTA_PARA_CAJA", "VENCIDA"):
        op.execute(f"ALTER TYPE estado_reserva ADD VALUE IF NOT EXISTS '{valor}'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL no permite quitar valores de un enum sin recrear el tipo
    # completo (y migrar cualquier fila que ya los use) -- riesgoso para una
    # migración pensada como "mínima y segura" (ver CU20). Se deja como
    # no-op a propósito: bajar esta revisión no restaura el enum anterior,
    # pero tampoco arriesga ni borra ningún dato existente.
    pass
