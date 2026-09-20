"""extend venta for cu24 (venta presencial)

Revision ID: a7f21c4d9b3e
Revises: f3c9d6e2a815
Create Date: 2026-09-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7f21c4d9b3e'
down_revision: Union[str, Sequence[str], None] = 'f3c9d6e2a815'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. CU24 agrega PRESENCIAL a tipo_venta -- mismo patrón ya usado para
    #    ampliar estado_venta (PAGADA, CU23) y estado_reserva (CU20).
    op.execute("ALTER TYPE tipo_venta ADD VALUE IF NOT EXISTS 'PRESENCIAL'")

    # 2. cliente_id ahora es NULLABLE -- una venta presencial DIRECTA (CU24)
    #    no exige registrar un Cliente (ver Models/venta.py).
    op.alter_column('ventas', 'cliente_id', existing_type=sa.Integer(), nullable=True)

    # 3. cajero_id -- quién registró la venta (NULL para DIGITAL, CU22).
    op.add_column('ventas', sa.Column('cajero_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_ventas_cajero_id', 'ventas', 'usuarios', ['cajero_id'], ['id'])

    # 4. origen -- DIRECTA/RESERVA, solo aplica a PRESENCIAL.
    origen_venta = sa.Enum('DIRECTA', 'RESERVA', name='origen_venta')
    origen_venta.create(op.get_bind(), checkfirst=True)
    op.add_column('ventas', sa.Column('origen', origen_venta, nullable=True))

    # 5. reserva_id -- la Reserva LISTA_PARA_CAJA de la que salió la venta
    #    (solo cuando origen == RESERVA).
    op.add_column('ventas', sa.Column('reserva_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_ventas_reserva_id', 'ventas', 'reservas', ['reserva_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_ventas_reserva_id', 'ventas', type_='foreignkey')
    op.drop_column('ventas', 'reserva_id')

    op.drop_column('ventas', 'origen')
    sa.Enum(name='origen_venta').drop(op.get_bind(), checkfirst=True)

    op.drop_constraint('fk_ventas_cajero_id', 'ventas', type_='foreignkey')
    op.drop_column('ventas', 'cajero_id')

    # cliente_id se deja NULLABLE en el downgrade a propósito: forzar NOT
    # NULL de nuevo rompería si ya existe alguna venta PRESENCIAL DIRECTA
    # con cliente_id nulo -- mismo criterio "downgrade nunca arriesga datos"
    # ya usado en las migraciones de CU20/CU23.
    #
    # PostgreSQL tampoco permite quitar un valor de un enum sin recrear el
    # tipo completo -- 'PRESENCIAL' se queda (mismo criterio).
