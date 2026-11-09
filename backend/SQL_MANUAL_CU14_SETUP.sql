-- ============================================================================
-- SCRIPT MANUAL SQL PARA CREAR TABLA CU14
-- Tabla: conflictos_sincronizacion
-- Fecha: 2026-11-09
-- ============================================================================
-- INSTRUCCIONES:
-- 1. Ejecutar respaldo de PostgreSQL ANTES de este script
-- 2. NO ejecutar este script hasta recibir autorización expresa
-- 3. Ejecutar como usuario fashionstore en base de datos fashionstore
-- 4. Script es IDEMPOTENTE (IF NOT EXISTS)
-- ============================================================================

-- ============================================================================
-- CREAR TABLA conflictos_sincronizacion
-- ============================================================================

CREATE TABLE IF NOT EXISTS conflictos_sincronizacion (
    -- Clave primaria (SQLAlchemy: id: Mapped[int] = mapped_column(Integer, primary_key=True))
    id SERIAL PRIMARY KEY,

    -- Identificadores (Líneas 25-27 en modelo)
    empresa_id INTEGER NOT NULL,  -- Mapped[int] mapped_column(Integer, nullable=False, index=True)
    uuid_operacion_offline VARCHAR(255) NOT NULL,  -- Mapped[str] mapped_column(String(255), nullable=False, index=True)
    tipo_operacion VARCHAR(50) NOT NULL,  -- Mapped[str] mapped_column(String(50), nullable=False)

    -- Clasificación de conflicto (Línea 30-31)
    tipo_conflicto VARCHAR(100) NOT NULL,  -- Mapped[str] mapped_column(String(100), nullable=False)
    estado_conflicto VARCHAR(50) NOT NULL DEFAULT 'DETECTADO',  -- Mapped[str] mapped_column(String(50), nullable=False, default="DETECTADO")

    -- Detalles del conflicto (Línea 34-35)
    motivo VARCHAR(500),  -- Mapped[str | None] mapped_column(String(500), nullable=True)
    detalles_conflicto VARCHAR(2000),  -- Mapped[str | None] mapped_column(String(2000), nullable=True)

    -- Auditoría temporal (Línea 38-39)
    fecha_detectado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Mapped[datetime] mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_resolucion TIMESTAMP,  -- Mapped[datetime | None] mapped_column(DateTime, nullable=True)

    -- Contexto de usuarios (Línea 42-43)
    usuario_id INTEGER,  -- Mapped[int | None] mapped_column(Integer, nullable=True)
    usuario_resolucion_id INTEGER,  -- Mapped[int | None] mapped_column(Integer, nullable=True)

    -- Prevención de reintentos automáticos (Línea 46-48)
    debe_reintentarse_automaticamente BOOLEAN NOT NULL DEFAULT false  -- Mapped[bool] mapped_column(Boolean, nullable=False, default=False)
);

-- ============================================================================
-- CREAR ÍNDICES COMPUESTOS (Línea 50-53 en modelo)
-- ============================================================================

-- idx_uuid_empresa_cu14: Index('idx_uuid_empresa_cu14', 'uuid_operacion_offline', 'empresa_id')
CREATE INDEX IF NOT EXISTS idx_uuid_empresa_cu14
    ON conflictos_sincronizacion(uuid_operacion_offline, empresa_id);

-- idx_empresa_estado_cu14: Index('idx_empresa_estado_cu14', 'empresa_id', 'estado_conflicto')
CREATE INDEX IF NOT EXISTS idx_empresa_estado_cu14
    ON conflictos_sincronizacion(empresa_id, estado_conflicto);

-- idx_empresa_tipo_cu14: Index('idx_empresa_tipo_cu14', 'empresa_id', 'tipo_conflicto')
CREATE INDEX IF NOT EXISTS idx_empresa_tipo_cu14
    ON conflictos_sincronizacion(empresa_id, tipo_conflicto);

-- idx_empresa_fecha_cu14: Index('idx_empresa_fecha_cu14', 'empresa_id', 'fecha_detectado')
CREATE INDEX IF NOT EXISTS idx_empresa_fecha_cu14
    ON conflictos_sincronizacion(empresa_id, fecha_detectado);

-- ============================================================================
-- VERIFICACIONES POSTERIORES (ejecutar DESPUÉS de la tabla creada)
-- ============================================================================

-- Verificación 1: Confirmar que la tabla fue creada correctamente
-- Expected: 1 row
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_name='conflictos_sincronizacion';

-- Verificación 2: Verificar todas las columnas (12 columnas esperadas)
-- Expected: 12 rows
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema='public' AND table_name='conflictos_sincronizacion'
ORDER BY ordinal_position;

-- Verificación 3: Verificar índices (4 esperados: 1 PK + 3 compuestos)
-- Expected: 4 rows
SELECT indexname FROM pg_indexes
WHERE tablename='conflictos_sincronizacion';

-- Verificación 4: Contar filas (debe estar vacía inicialmente)
-- Expected: 0 rows
SELECT COUNT(*) as total_registros FROM conflictos_sincronizacion;

-- Verificación 5: Verificar que no se modificó ninguna otra tabla
-- Expected: >0 rows (todas las tablas normales deberían aparecer)
SELECT tablename FROM pg_tables
WHERE schemaname='public'
ORDER BY tablename;

-- Fin del script
