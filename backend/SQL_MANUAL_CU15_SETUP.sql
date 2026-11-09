-- SQL MANUAL CU15 — Crear tabla reconciliacion_inventario
-- Fecha: 2026-11-09
-- Propósito: Auditoría de reconciliaciones de inventario (verificación sin ajustes)

-- ============================================================================
-- 1. CREAR TABLA (IDEMPOTENTE)
-- ============================================================================

CREATE TABLE IF NOT EXISTS reconciliacion_inventario (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    sucursal_id INTEGER NOT NULL,
    uuid_operacion_offline VARCHAR(255) NOT NULL,
    tipo_operacion VARCHAR(50) NOT NULL,
    estado_general VARCHAR(50) NOT NULL,
    detalles_json TEXT,
    motivo_inconsistencia VARCHAR(500),
    fecha_reconciliacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. CREAR ÍNDICES (PERFORMANCE)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_cu15_uuid_empresa
    ON reconciliacion_inventario(empresa_id, uuid_operacion_offline);

CREATE INDEX IF NOT EXISTS idx_cu15_empresa_estado
    ON reconciliacion_inventario(empresa_id, estado_general);

CREATE INDEX IF NOT EXISTS idx_cu15_empresa_fecha
    ON reconciliacion_inventario(empresa_id, fecha_reconciliacion DESC);

-- ============================================================================
-- 3. VERIFICACIÓN DE ESTRUCTURA
-- ============================================================================

-- Verificar que la tabla existe y tiene estructura correcta
SELECT
    tablename,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_name='reconciliacion_inventario') as columnas
FROM pg_tables
WHERE tablename='reconciliacion_inventario';

-- Listar columnas
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name='reconciliacion_inventario'
ORDER BY ordinal_position;

-- Listar índices
SELECT indexname FROM pg_indexes
WHERE tablename='reconciliacion_inventario'
ORDER BY indexname;

-- ============================================================================
-- 4. ESTADÍSTICAS INICIALES
-- ============================================================================

SELECT
    'reconciliacion_inventario' as tabla,
    COUNT(*) as registros,
    pg_size_pretty(pg_total_relation_size('reconciliacion_inventario')) as tamaño
FROM reconciliacion_inventario;
