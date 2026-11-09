"""Crear tabla operaciones_sincronizacion_log para CU13.

Revision ID: 003_crear_operaciones_sincronizacion_log
Revises: a7ff7394dd64
Create Date: 2026-11-09
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003_crear_operaciones_sincronizacion_log'
down_revision = 'a7ff7394dd64'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crear tabla de auditoría de sincronización."""
    op.create_table(
        'operaciones_sincronizacion_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('uuid_operacion_offline', sa.String(255), nullable=False),
        sa.Column('tipo_operacion', sa.String(50), nullable=False),
        sa.Column('numero_intento', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('fecha_intento', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('estado_resultado', sa.String(20), nullable=False),
        sa.Column('motivo', sa.String(500), nullable=True),
        sa.Column('error_tipo', sa.String(100), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('tiempo_respuesta_ms', sa.Integer(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_uuid_empresa', 'operaciones_sincronizacion_log', ['uuid_operacion_offline', 'empresa_id'])
    op.create_index('idx_empresa_tipo_estado', 'operaciones_sincronizacion_log', ['empresa_id', 'tipo_operacion', 'estado_resultado'])
    op.create_index('idx_empresa_fecha', 'operaciones_sincronizacion_log', ['empresa_id', 'fecha_intento'])


def downgrade() -> None:
    """Eliminar tabla (solo para rollback)."""
    op.drop_index('idx_empresa_fecha', table_name='operaciones_sincronizacion_log')
    op.drop_index('idx_empresa_tipo_estado', table_name='operaciones_sincronizacion_log')
    op.drop_index('idx_uuid_empresa', table_name='operaciones_sincronizacion_log')
    op.drop_table('operaciones_sincronizacion_log')
