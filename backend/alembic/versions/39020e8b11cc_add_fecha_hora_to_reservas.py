"""add fecha_reserva/hora_inicio to reservas

Revision ID: 39020e8b11cc
Revises: ca440f73d20a
Create Date: 2026-09-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39020e8b11cc'
down_revision: Union[str, Sequence[str], None] = 'ca440f73d20a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Se agregan nullable primero para poder rellenar las filas existentes
    # (reservas ya creadas antes de esta migración) sin perderlas: fecha_reserva
    # toma el día en que la reserva se creó y hora_inicio cae en la apertura
    # (10:00) -- un valor de respaldo razonable, no inventado al azar, ya que
    # esas reservas no tenían horario real todavía.
    op.add_column('reservas', sa.Column('fecha_reserva', sa.Date(), nullable=True))
    op.add_column('reservas', sa.Column('hora_inicio', sa.Time(), nullable=True))
    op.execute(
        "UPDATE reservas SET fecha_reserva = fecha_creacion::date, hora_inicio = '10:00:00' "
        "WHERE fecha_reserva IS NULL"
    )
    op.alter_column('reservas', 'fecha_reserva', nullable=False)
    op.alter_column('reservas', 'hora_inicio', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reservas', 'hora_inicio')
    op.drop_column('reservas', 'fecha_reserva')
