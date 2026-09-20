"""split reserva into cabecera + detalle (una reserva, varias prendas)

Revision ID: 7a1c9e4f2b3d
Revises: 55108991ff6f
Create Date: 2026-09-16 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum


# revision identifiers, used by Alembic.
revision: str = '7a1c9e4f2b3d'
down_revision: Union[str, Sequence[str], None] = '55108991ff6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Separa la tabla `reservas` (antes: una fila = una prenda) en una
    cabecera `reservas` (visita del Cliente: cliente+sucursal+fecha/hora+
    código visible) y un detalle `reserva_detalles` (una prenda dentro de
    esa visita, con su propio estado) -- ver Models/reserva.py para el
    modelo resultante.

    NO borra ninguna fila existente. Estrategia:
      1. Renombra la tabla actual `reservas` a `reserva_detalles`: cada fila
         existente se conserva TAL CUAL (mismo id, mismo estado, mismos
         datos) y se convierte en el detalle de su propia cabecera nueva.
      2. Crea la tabla `reservas` (cabecera) desde cero.
      3. Por cada fila de `reserva_detalles` (la vieja `reservas`) inserta
         UNA cabecera con sus datos de cliente/sucursal/fecha/hora/estado --
         1 reserva vieja = 1 cabecera + 1 detalle.
      4. Enlaza cada detalle con su cabecera nueva (`reserva_id`) y genera
         su `codigo_reserva` (RS-00001, ...) a partir del id DEFINITIVO de
         esa cabecera.
      5. Quita de `reserva_detalles` las columnas que ahora viven SOLO en la
         cabecera (cliente_id, sucursal_id, fecha_reserva, hora_inicio,
         fecha_creacion) y deja `reserva_id` NOT NULL con su FK.
    """
    # -- 1. La tabla actual pasa a ser el detalle; conserva sus datos y sus
    # constraints (solo se renombran para que coincidan con la tabla nueva --
    # renombrar una tabla en Postgres NO renombra sus constraints/secuencia).
    op.rename_table('reservas', 'reserva_detalles')
    op.execute('ALTER TABLE reserva_detalles RENAME CONSTRAINT reservas_pkey TO reserva_detalles_pkey')
    op.execute(
        'ALTER TABLE reserva_detalles RENAME CONSTRAINT ck_reserva_cantidad_positiva '
        'TO ck_reserva_detalle_cantidad_positiva'
    )
    op.execute(
        'ALTER TABLE reserva_detalles RENAME CONSTRAINT reservas_producto_variante_id_fkey '
        'TO reserva_detalles_producto_variante_id_fkey'
    )
    op.execute('ALTER SEQUENCE reservas_id_seq RENAME TO reserva_detalles_id_seq')

    # -- 2. Tabla cabecera nueva. codigo_reserva nullable=True de momento --
    # se completa en el paso 4, una vez que cada cabecera ya tiene su id
    # definitivo (el código se arma a partir de ESE id, no del id de la fila
    # vieja que la originó). create_type=False: el tipo enum 'estado_reserva'
    # ya existe (creado por ca440f73d20a / ampliado por 55108991ff6f).
    op.create_table(
        'reservas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo_reserva', sa.String(length=20), nullable=True),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('sucursal_id', sa.Integer(), nullable=False),
        sa.Column('fecha_reserva', sa.Date(), nullable=False),
        sa.Column('hora_inicio', sa.Time(), nullable=False),
        sa.Column(
            'estado_general',
            PGEnum(
                'PENDIENTE', 'PREPARADA', 'EN_ATENCION', 'LISTA_PARA_CAJA', 'CANCELADA', 'ATENDIDA', 'VENCIDA',
                name='estado_reserva',
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['sucursal_id'], ['sucursales.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # -- 3. Una cabecera por cada detalle existente. `_detalle_origen_id` es
    # una columna temporal SOLO para el paso 4 -- se elimina al final.
    op.add_column('reservas', sa.Column('_detalle_origen_id', sa.Integer(), nullable=True))
    op.execute(
        """
        INSERT INTO reservas (
            cliente_id, sucursal_id, fecha_reserva, hora_inicio, estado_general,
            fecha_creacion, _detalle_origen_id
        )
        SELECT cliente_id, sucursal_id, fecha_reserva, hora_inicio, estado,
               fecha_creacion, id
        FROM reserva_detalles
        ORDER BY id
        """
    )

    # -- 4. Enlaza cada detalle con la cabecera que se creó a partir de él, y
    # genera el código visible (RS-00001, ...) a partir del id DEFINITIVO de
    # la cabecera -- nunca del id del detalle que la originó.
    op.add_column('reserva_detalles', sa.Column('reserva_id', sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE reserva_detalles AS rd
        SET reserva_id = r.id
        FROM reservas AS r
        WHERE r._detalle_origen_id = rd.id
        """
    )
    op.execute("UPDATE reservas SET codigo_reserva = 'RS-' || lpad(id::text, 5, '0')")
    op.drop_column('reservas', '_detalle_origen_id')

    op.alter_column('reservas', 'codigo_reserva', nullable=False)
    op.create_unique_constraint('uq_reservas_codigo_reserva', 'reservas', ['codigo_reserva'])
    op.alter_column('reserva_detalles', 'reserva_id', nullable=False)
    op.create_foreign_key(
        'fk_reserva_detalles_reserva_id', 'reserva_detalles', 'reservas', ['reserva_id'], ['id'], ondelete='CASCADE'
    )
    op.create_index('ix_reserva_detalles_reserva_id', 'reserva_detalles', ['reserva_id'])

    # -- 5. Estas columnas ahora viven SOLO en la cabecera.
    op.drop_constraint('reservas_cliente_id_fkey', 'reserva_detalles', type_='foreignkey')
    op.drop_constraint('reservas_sucursal_id_fkey', 'reserva_detalles', type_='foreignkey')
    op.drop_column('reserva_detalles', 'cliente_id')
    op.drop_column('reserva_detalles', 'sucursal_id')
    op.drop_column('reserva_detalles', 'fecha_reserva')
    op.drop_column('reserva_detalles', 'hora_inicio')
    op.drop_column('reserva_detalles', 'fecha_creacion')


def downgrade() -> None:
    """No reversible de forma segura: en cuanto una cabecera agrupe más de
    un detalle (el objetivo mismo de esta migración), ya no existe una fila
    "reservas" antigua equivalente a la que volver sin perder información --
    mismo criterio de downgrade no-op ya documentado en 55108991ff6f para no
    arriesgar ni borrar datos reales."""
    pass
