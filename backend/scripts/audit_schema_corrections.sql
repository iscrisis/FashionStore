-- =============================================================================
-- AUDITORÍA INTEGRAL: CORRECCIONES DE SINCRONIZACIÓN
-- Base de datos: fashionstore
-- Fecha: 2026-10-31
-- =============================================================================
--
-- Este script corrige las diferencias entre los modelos SQLAlchemy
-- y el esquema actual de PostgreSQL.
--
-- RESTRICCIONES:
-- ✓ NO DESTRUCTIVO: solo ADD COLUMN, sin DROP, DELETE, TRUNCATE
-- ✓ DATA SAFE: respeta todos los datos existentes
-- ✓ IDEMPOTENTE: usa IF NOT EXISTS para operaciones seguras
-- ✓ NO MULTITENANT: no asigna empresas arbitrariamente
-- ✓ SIN MODIFICACIÓN DE DATOS: no altera registros existentes
--
-- =============================================================================

-- FASE: CORRECCIONES POR TABLA
-- =============================================================================

-- 1. TABLA: producto_variantes
-- STATUS: PARCIALMENTE FIJO (columna agregada manualmente el 2026-10-31)
-- DESCRIPCIÓN: Se agregó columna is_active que faltaba en la BD original
--
-- VERIFICACIÓN: Ya existe después de ALTER TABLE ejecutado
-- ACCIÓN: No requiere corrección adicional

ALTER TABLE IF EXISTS producto_variantes
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;


-- 2. TABLA: colecciones
-- STATUS: INCOMPLETA
-- DESCRIPCIÓN: Faltan 2 columnas definidas en el modelo Coleccion para soporte CU10
--
-- REFERENCIA: backend/modules/P1_SucursalesYCatalogos/Models/coleccion.py (líneas 39-40)
-- MODELO ESPERA:
--   - es_destacada_inicio: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
--   - imagen_destacada_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
--
-- IMPACTO:
--   - CRÍTICA: Intenta seleccionar estas columnas al listar colecciones → Error 500
--   - Afecta a: CU10 (Gestionar temporadas y colecciones), Panel cliente (Home hero)

ALTER TABLE IF EXISTS colecciones
  ADD COLUMN IF NOT EXISTS es_destacada_inicio BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE IF EXISTS colecciones
  ADD COLUMN IF NOT EXISTS imagen_destacada_url VARCHAR(500) NULL;

-- COMMENT: Define cuál colección aparece en el home del cliente
-- Una sola colección por empresa debe estar marcada como destacada


-- =============================================================================
-- VERIFICACIÓN FINAL
-- =============================================================================

-- Listar cambios aplicados
SELECT
  table_name,
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('producto_variantes', 'colecciones')
ORDER BY table_name, ordinal_position;
