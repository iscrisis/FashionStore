-- ============================================================================
-- SCRIPT MANUAL SQL PARA HABILITAR CU13
-- Tabla: operaciones_sincronizacion_log
-- Fecha: 2026-11-09
-- ============================================================================
-- INSTRUCCIONES:
-- 1. Ejecutar respaldo de PostgreSQL ANTES de este script
-- 2. NO ejecutar este script hasta recibir autorización expresa
-- 3. Ejecutar como usuario fashionstore en base de datos fashionstore
-- 4. NO ejecutar Alembic ni usar alembic stamp
-- 5. Verificar integridad después de ejecutar
-- ============================================================================

-- ============================================================================
-- SECCIÓN 1: CREAR TABLA operaciones_sincronizacion_log
-- ============================================================================

CREATE TABLE IF NOT EXISTS operaciones_sincronizacion_log (
    -- Clave primaria (SQLAlchemy: id: Mapped[int] = mapped_column(Integer, primary_key=True))
    id SERIAL PRIMARY KEY,

    -- Identificadores (Línea 25-26 en modelo)
    empresa_id INTEGER NOT NULL,  -- Mapped[int] mapped_column(Integer, nullable=False, index=True)
    uuid_operacion_offline VARCHAR(255) NOT NULL,  -- Mapped[str] mapped_column(String(255), nullable=False, index=True)
    tipo_operacion VARCHAR(50) NOT NULL,  -- Mapped[str] mapped_column(String(50), nullable=False)

    -- Intento (Línea 30-31)
    numero_intento INTEGER NOT NULL DEFAULT 1,  -- Mapped[int] mapped_column(Integer, nullable=False, default=1)
    fecha_intento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Mapped[datetime] mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    -- Resultado (Línea 34-35)
    estado_resultado VARCHAR(20) NOT NULL,  -- Mapped[str] mapped_column(String(20), nullable=False)
    motivo VARCHAR(500),  -- Mapped[str | None] mapped_column(String(500), nullable=True)

    -- Error (Línea 38-40)
    error_tipo VARCHAR(100),  -- Mapped[str | None] mapped_column(String(100), nullable=True)
    http_status INTEGER,  -- Mapped[int | None] mapped_column(Integer, nullable=True)
    tiempo_respuesta_ms INTEGER,  -- Mapped[int | None] mapped_column(Integer, nullable=True)

    -- Contexto (Línea 43)
    usuario_id INTEGER  -- Mapped[int | None] mapped_column(Integer, nullable=True)
);

-- ============================================================================
-- SECCIÓN 2: CREAR ÍNDICES COMPUESTOS (Línea 46-49 en modelo)
-- ============================================================================

-- idx_uuid_empresa: Index('idx_uuid_empresa', 'uuid_operacion_offline', 'empresa_id')
CREATE INDEX IF NOT EXISTS idx_uuid_empresa
    ON operaciones_sincronizacion_log(uuid_operacion_offline, empresa_id);

-- idx_empresa_tipo_estado: Index('idx_empresa_tipo_estado', 'empresa_id', 'tipo_operacion', 'estado_resultado')
CREATE INDEX IF NOT EXISTS idx_empresa_tipo_estado
    ON operaciones_sincronizacion_log(empresa_id, tipo_operacion, estado_resultado);

-- idx_empresa_fecha: Index('idx_empresa_fecha', 'empresa_id', 'fecha_intento')
CREATE INDEX IF NOT EXISTS idx_empresa_fecha
    ON operaciones_sincronizacion_log(empresa_id, fecha_intento);

-- ============================================================================
-- SECCIÓN 3: VERIFICACIONES POSTERIORES (ejecutar DESPUÉS de la tabla creada)
-- ============================================================================

-- Verificación 1: Confirmar que la tabla fue creada correctamente
-- Expected: 1 row
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_name='operaciones_sincronizacion_log';

-- Verificación 2: Verificar todas las columnas
-- Expected: 13 rows con nombres exactos
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema='public' AND table_name='operaciones_sincronizacion_log'
ORDER BY ordinal_position;

-- Verificación 3: Verificar índices
-- Expected: 3 índices (idx_uuid_empresa, idx_empresa_tipo_estado, idx_empresa_fecha)
SELECT indexname FROM pg_indexes
WHERE tablename='operaciones_sincronizacion_log';

-- Verificación 4: Contar filas (debe estar vacía inicialmente)
-- Expected: 0 rows
SELECT COUNT(*) as total_registros FROM operaciones_sincronizacion_log;

-- Verificación 5: Verificar que no se modificó ninguna otra tabla
-- Expected: 0 rows (no hay modificaciones recientes en otras tablas)
SELECT tablename FROM pg_tables
WHERE schemaname='public' AND tablename NOT IN (
    SELECT tablename FROM pg_tables WHERE schemaname='public'
    AND tablename IN ('usuarios', 'empresas', 'sucursales', 'ventas', 'reservas',
                      'pagos', 'stock_sucursal', 'productos', 'producto_variantes',
                      'carritos', 'carrito_items', 'devoluciones_cambios', 'pagos')
)
AND tablename != 'operaciones_sincronizacion_log'
ORDER BY tablename;

-- Fin del script
