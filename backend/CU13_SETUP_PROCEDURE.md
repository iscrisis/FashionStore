# Procedimiento de Activación Manual de CU13

**Fecha:** 2026-11-09  
**Estado:** PREPARADO PARA AUTORIZACIÓN  
**Riesgo:** BAJO (solo crea una tabla nueva, no modifica existentes)

---

## 1. COMPARACIÓN: Modelo SQLAlchemy vs. Script SQL

| Elemento | SQLAlchemy (modelo) | SQL Script | ✓ Match |
|----------|-------------------|-----------|---------|
| **Tabla** | `__tablename__ = "operaciones_sincronizacion_log"` | CREATE TABLE operaciones_sincronizacion_log | ✓ |
| **id** | `mapped_column(Integer, primary_key=True)` | SERIAL PRIMARY KEY | ✓ |
| **empresa_id** | `Integer, nullable=False, index=True` | INTEGER NOT NULL (con idx_uuid_empresa) | ✓ |
| **uuid_operacion_offline** | `String(255), nullable=False, index=True` | VARCHAR(255) NOT NULL (con idx_uuid_empresa) | ✓ |
| **tipo_operacion** | `String(50), nullable=False` | VARCHAR(50) NOT NULL | ✓ |
| **numero_intento** | `Integer, nullable=False, default=1` | INTEGER NOT NULL DEFAULT 1 | ✓ |
| **fecha_intento** | `DateTime, nullable=False, default=datetime.utcnow` | TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP | ✓ |
| **estado_resultado** | `String(20), nullable=False` | VARCHAR(20) NOT NULL | ✓ |
| **motivo** | `String(500), nullable=True` | VARCHAR(500) | ✓ |
| **error_tipo** | `String(100), nullable=True` | VARCHAR(100) | ✓ |
| **http_status** | `Integer, nullable=True` | INTEGER | ✓ |
| **tiempo_respuesta_ms** | `Integer, nullable=True` | INTEGER | ✓ |
| **usuario_id** | `Integer, nullable=True` | INTEGER | ✓ |
| **idx_uuid_empresa** | `Index('idx_uuid_empresa', 'uuid_operacion_offline', 'empresa_id')` | CREATE INDEX idx_uuid_empresa ON ... (uuid_operacion_offline, empresa_id) | ✓ |
| **idx_empresa_tipo_estado** | `Index('idx_empresa_tipo_estado', 'empresa_id', 'tipo_operacion', 'estado_resultado')` | CREATE INDEX idx_empresa_tipo_estado ON ... (empresa_id, tipo_operacion, estado_resultado) | ✓ |
| **idx_empresa_fecha** | `Index('idx_empresa_fecha', 'empresa_id', 'fecha_intento')` | CREATE INDEX idx_empresa_fecha ON ... (empresa_id, fecha_intento) | ✓ |

**Conclusión:** 100% compatible. Script SQL replica exactamente el modelo SQLAlchemy.

---

## 2. VERIFICACIÓN: Script NO modifica tablas existentes

Script SQL SOLO:
- ✅ CREATE TABLE IF NOT EXISTS — solo crea si no existe
- ✅ CREATE INDEX IF NOT EXISTS — solo crea si no existe
- ❌ NO DROP, ALTER, UPDATE ni DELETE
- ❌ NO modifica estructuras existentes

Tablas que permanecen intactas:
- ✅ usuarios
- ✅ empresas
- ✅ sucursales
- ✅ ventas
- ✅ reservas
- ✅ pagos
- ✅ stock_sucursal
- ✅ productos
- ✅ producto_variantes
- ✅ carritos
- ✅ carrito_items
- ✅ devoluciones_cambios
- ✅ (todas las demás)

---

## 3. PROCEDIMIENTO DE RESPALDO PREVIO

### Pre-ejecución (antes de ejecutar script SQL)

```bash
# 1. Conectar a contenedor PostgreSQL
docker exec fashionstore-db-1 bash

# 2. Crear respaldo completo de la BD
BACKUP_FILE="/backups/fashionstore_backup_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p /backups
pg_dump -U fashionstore -d fashionstore > "$BACKUP_FILE"

# 3. Verificar que el respaldo se creó
ls -lh "$BACKUP_FILE"

# 4. Comprimir el respaldo (opcional pero recomendado)
gzip "$BACKUP_FILE"

# 5. Salir del contenedor
exit

# 6. Copiar respaldo a máquina host (para mayor seguridad)
docker cp fashionstore-db-1:/backups/. ./postgres_backup_$(date +%Y%m%d_%H%M%S)/
```

### Verificar respaldo

```bash
# Verificar que el archivo existe y tiene contenido
du -h postgres_backup_*/fashionstore_backup*.sql.gz

# Listar contenido del respaldo (verificar que incluye operaciones)
zcat postgres_backup_*/fashionstore_backup*.sql.gz | grep -c "^CREATE"
```

---

## 4. PROCEDIMIENTO DE EJECUCIÓN (CUANDO SE AUTORICE)

### Ejecutar script SQL

```bash
# 1. Desde dentro del contenedor PostgreSQL
docker exec -i fashionstore-db-1 psql -U fashionstore -d fashionstore < SQL_MANUAL_CU13_SETUP.sql

# 2. SALIDA ESPERADA:
# CREATE TABLE
# CREATE INDEX
# (13 filas con columnas)
# (3 índices)
# (0 registros)
# (0 filas de modificaciones)
```

---

## 5. VERIFICACIONES POSTERIORES A LA EJECUCIÓN

### Verificación 1: Tabla creada correctamente

```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' AND table_name='operaciones_sincronizacion_log';
```

**Resultado esperado:** 1 fila con `operaciones_sincronizacion_log`

### Verificación 2: Columnas correctas

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema='public' AND table_name='operaciones_sincronizacion_log'
ORDER BY ordinal_position;
```

**Resultado esperado:** 13 columnas exactas (id, empresa_id, uuid_operacion_offline, tipo_operacion, numero_intento, fecha_intento, estado_resultado, motivo, error_tipo, http_status, tiempo_respuesta_ms, usuario_id)

### Verificación 3: Índices creados

```sql
SELECT indexname FROM pg_indexes
WHERE tablename='operaciones_sincronizacion_log';
```

**Resultado esperado:** 3 índices (idx_uuid_empresa, idx_empresa_tipo_estado, idx_empresa_fecha)

### Verificación 4: Tabla vacía

```sql
SELECT COUNT(*) as total_registros FROM operaciones_sincronizacion_log;
```

**Resultado esperado:** 0 filas

### Verificación 5: CU13 puede utilizar la tabla

```bash
# Desde el contenedor backend, ejecutar prueba de conexión
docker exec fashionstore-backend-1 python -c "
from modules.Models.operacion_sincronizacion_log import OperacionSincronizacionLog
from sqlalchemy import create_engine, text
import os

engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM operaciones_sincronizacion_log'))
    print(f'✓ CU13 tabla accesible: {result.scalar()} registros')
"
```

**Resultado esperado:** `✓ CU13 tabla accesible: 0 registros`

---

## 6. PROCEDIMIENTO DE ROLLBACK (SI ES NECESARIO)

### Si algo falla

```bash
# 1. Restaurar desde respaldo
docker exec -i fashionstore-db-1 psql -U fashionstore -d fashionstore < postgres_backup_YYYYMMDD_HHMMSS/fashionstore_backup_YYYYMMDD_HHMMSS.sql

# 2. Verificar que se restauró
docker exec fashionstore-db-1 psql -U fashionstore -d fashionstore -c "
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema='public' AND table_name='operaciones_sincronizacion_log';"

# Resultado esperado: 0 filas (tabla eliminada)
```

---

## 7. IMPACTO EN OTROS CASOS DE USO

### Tabla independiente
- ✅ NO toca ventas (CU8, CU9, CU11)
- ✅ NO toca reservas (CU8, CU11)
- ✅ NO toca inventario (stock_sucursal, movimientos_inventario)
- ✅ NO toca pagos
- ✅ NO toca usuarios

### Solo CU13 accede
- ✅ ConnectivityService: no modificado
- ✅ OfflineAutoSyncCU11Service: no modificado
- ✅ offline-storage.service.ts: no modificado

---

## 8. RESUMEN: Seguridad del Procedimiento

| Aspecto | Estado | Riesgo |
|---------|--------|--------|
| **Script es aditivo** | ✅ Solo CREATE | BAJO |
| **No modifica existentes** | ✅ IF NOT EXISTS | BAJO |
| **Tabla independiente** | ✅ Aislada | BAJO |
| **Respaldo disponible** | ✅ Pre-ejecución | BAJO |
| **Rollback posible** | ✅ Desde respaldo | BAJO |
| **CU13 código listo** | ✅ Revisado | BAJO |

**Riesgo General: BAJO**

---

## 9. CHECKLIST PRE-EJECUCIÓN

Antes de ejecutar, verificar:

- [ ] Respaldo de PostgreSQL creado y verificado
- [ ] Script SQL SQL_MANUAL_CU13_SETUP.sql disponible
- [ ] Usuario fashionstore tiene permisos en DB fashionstore
- [ ] CU13 código está en repo (servicios, componentes, modelos)
- [ ] Nadie está utilizando la BD durante la ejecución
- [ ] Ventana de mantenimiento programada (si es necesario)

---

**Estado Final:** Procedimiento LISTO PARA AUTORIZACIÓN  
**Próximo paso:** Aguardando confirmación del usuario para ejecutar script SQL

