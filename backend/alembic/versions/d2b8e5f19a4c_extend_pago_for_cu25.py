"""extend pago for cu25 (pago presencial)

Revision ID: d2b8e5f19a4c
Revises: a7f21c4d9b3e
Create Date: 2026-09-19 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2b8e5f19a4c'
down_revision: Union[str, Sequence[str], None] = 'a7f21c4d9b3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. CU25 agrega EFECTIVO/TARJETA/QR a proveedor_pago -- mismo campo que
    #    ya usaba CU23 para STRIPE, ahora también sirve como "método de
    #    pago" del mostrador (mismo patrón ya usado para tipo_venta/
    #    estado_venta: ALTER TYPE ADD VALUE, sin recrear el tipo).
    op.execute("ALTER TYPE proveedor_pago ADD VALUE IF NOT EXISTS 'EFECTIVO'")
    op.execute("ALTER TYPE proveedor_pago ADD VALUE IF NOT EXISTS 'TARJETA'")
    op.execute("ALTER TYPE proveedor_pago ADD VALUE IF NOT EXISTS 'QR'")

    # 2. stripe_checkout_session_id ahora es NULLABLE -- un pago presencial
    #    (CU25) no tiene sesión de Stripe. Sigue UNIQUE: Postgres permite
    #    múltiples NULL sin conflicto.
    op.alter_column(
        'pagos', 'stripe_checkout_session_id', existing_type=sa.String(length=255), nullable=True
    )

    # 3. cajero_id -- quién registró el pago presencial (NULL para STRIPE).
    op.add_column('pagos', sa.Column('cajero_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_pagos_cajero_id', 'pagos', 'usuarios', ['cajero_id'], ['id'])

    # 4. EFECTIVO: monto recibido y cambio calculado.
    op.add_column('pagos', sa.Column('monto_recibido', sa.Numeric(10, 2), nullable=True))
    op.add_column('pagos', sa.Column('cambio', sa.Numeric(10, 2), nullable=True))

    # 5. TARJETA: tipo (débito/crédito) y referencia opcional del POS.
    tipo_tarjeta = sa.Enum('DEBITO', 'CREDITO', name='tipo_tarjeta')
    tipo_tarjeta.create(op.get_bind(), checkfirst=True)
    op.add_column('pagos', sa.Column('tipo_tarjeta', tipo_tarjeta, nullable=True))

    # 6. TARJETA/QR: referencia opcional (nunca datos sensibles de tarjeta).
    op.add_column('pagos', sa.Column('referencia', sa.String(length=120), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('pagos', 'referencia')
    op.drop_column('pagos', 'tipo_tarjeta')
    sa.Enum(name='tipo_tarjeta').drop(op.get_bind(), checkfirst=True)
    op.drop_column('pagos', 'cambio')
    op.drop_column('pagos', 'monto_recibido')
    op.drop_constraint('fk_pagos_cajero_id', 'pagos', type_='foreignkey')
    op.drop_column('pagos', 'cajero_id')

    # stripe_checkout_session_id se deja NULLABLE en el downgrade a propósito
    # (ya podría haber filas de pagos presenciales con NULL ahí) -- mismo
    # criterio "downgrade nunca arriesga datos" ya usado en migraciones
    # anteriores. PostgreSQL tampoco permite quitar valores de un enum sin
    # recrear el tipo completo -- EFECTIVO/TARJETA/QR se quedan.
