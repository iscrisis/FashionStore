# Pruebas de Integración CU11 — Sincronizar Operaciones Pendientes

## Descripción

Suite de pruebas que valida la sincronización de ventas y reservas offline desde IndexedDB (frontend) a PostgreSQL (backend) sin duplicados y con atomicidad.

## Requisitos

- Docker y Docker Compose
- Python 3.8+
- Pip packages: `requests`, `psycopg2-binary`
- FastAPI backend compilado y listo para iniciar

## Configuración

### 1. Instalar dependencias

```bash
pip install requests psycopg2-binary
```

### 2. Iniciar PostgreSQL de pruebas (contenedor Docker)

```bash
cd /path/to/FashionStore

# Inicia contenedor PostgreSQL aislado en puerto 5433
docker-compose -f docker-compose.test.yml up -d

# Verificar que está listo
docker-compose -f docker-compose.test.yml logs postgres_test
```

**Esperar hasta ver:**
```
postgres_test | database system is ready to accept connections
```

### 3. Iniciar FastAPI backend

En una terminal diferente:

```bash
cd /path/to/FashionStore/backend

# Configurar variable de entorno para usar BD de pruebas
export DATABASE_URL="postgresql://test_user:test_password_secure@localhost:5433/fashionstore_test"

# Iniciar backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Esperar hasta ver:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. Ejecutar pruebas de integración

En una tercera terminal:

```bash
cd /path/to/FashionStore

# Ejecutar pruebas
python tests/test_cu11_integration.py

# O con pytest
pytest tests/test_cu11_integration.py -v -s
```

## Pruebas Incluidas

### Prueba 1: Sincronizar venta válida
- **Objetivo**: Verificar que una venta offline se sincroniza a PostgreSQL
- **Paso**: POST `/sincronizar/ventas` con venta válida
- **Validación**: 
  - Response HTTP 201
  - Estado "CONFIRMADA"
  - Venta aparece en tabla `ventas` con `uuid_operacion_offline`

### Prueba 2: Sincronizar reserva válida
- **Objetivo**: Verificar que una reserva offline se sincroniza a PostgreSQL
- **Paso**: POST `/sincronizar/reservas` con reserva válida
- **Validación**:
  - Response HTTP 201
  - Estado "CONFIRMADA"
  - Reserva aparece en tabla `reservas` con `uuid_operacion_offline`

### Prueba 3: Idempotencia — UUID duplicado
- **Objetivo**: Verificar que reenviando el mismo UUID no se crea duplicado
- **Paso**: POST `/sincronizar/ventas` con UUID que ya existe
- **Validación**:
  - Response HTTP 201 (no error)
  - Motivo contiene "idempotente"
  - Query: `SELECT COUNT(*) FROM ventas WHERE uuid_operacion_offline = ?` retorna 1 (no 2)

### Prueba 4: Stock deducido exactamente una vez
- **Objetivo**: Verificar que el inventario se descuenta una sola vez por venta
- **Paso**: 
  1. Leer stock antes
  2. POST `/sincronizar/ventas` con cantidad=5
  3. Leer stock después
- **Validación**: `stock_antes - stock_después == 5` (no 0, no 10)

## Resultados Esperados

```
============================================================
RESUMEN DE PRUEBAS DE INTEGRACIÓN CU11
============================================================
✓ PASS - test_1: Venta 1001
✓ PASS - test_2: Reserva 2001
✓ PASS - test_3: Idempotencia OK
✓ PASS - test_4: Stock -5 correctamente

Total: 4/4 pruebas aprobadas
============================================================
```

## Limpieza

### Detener contenedor PostgreSQL

```bash
docker-compose -f docker-compose.test.yml down

# Eliminar datos
docker-compose -f docker-compose.test.yml down -v
```

### Detener FastAPI backend

```bash
# Ctrl+C en la terminal donde está corriendo
```

## Troubleshooting

### Error: Connection refused (5433)

- Verificar que Docker está corriendo
- Esperar a que PostgreSQL esté listo: `docker-compose logs postgres_test`

### Error: 401 Unauthorized

- Auth es mock en pruebas
- Verificar que endpoint está retornando 404 (no 401)

### Error: SQLAlchemy/ORM

- Verificar que FastAPI está usando la BD correcta
- Revisar DATABASE_URL

### Tablas no existen

- Script crea tablas automáticamente
- Si falla, revisar permisos de usuario en PostgreSQL

## Notas

- Las pruebas usan una BD completamente aislada (`fashionstore_test`)
- No tocan Supabase compartida
- Datos de prueba se crean automáticamente
- Cada corrida empieza con esquema limpio

## Documentación de endpoints

### POST /sincronizar/ventas

Sincronizar venta presencial offline desde IndexedDB.

**Body:**
```json
{
  "uuid": "uuid-venta-001",
  "tipo_operacion": "VENTA_OFFLINE",
  "empresa_id": 100,
  "sucursal_id": 10,
  "fecha_operacion_local": "2026-11-08T12:00:00Z",
  "detalles": [
    {
      "producto_variante_id": 50,
      "cantidad": 2,
      "precio_unitario": 100.0,
      "subtotal": 200.0
    }
  ],
  "metodo_pago": "EFECTIVO",
  "monto_recibido": 250.0,
  "total": 200.0
}
```

**Response (201):**
```json
{
  "uuid_local": "uuid-venta-001",
  "venta_id": 1001,
  "codigo_venta": "V-20261108-001",
  "estado": "CONFIRMADA",
  "total": 200.0
}
```

### POST /sincronizar/reservas

Sincronizar reserva offline desde IndexedDB.

**Body:**
```json
{
  "uuid": "uuid-reserva-001",
  "tipo_operacion": "RESERVA_OFFLINE",
  "empresa_id": 100,
  "sucursal_id": 10,
  "cliente_id": 1,
  "fecha_reserva": "2026-11-15",
  "hora_inicio": "10:00",
  "detalles": [
    {
      "producto_variante_id": 50,
      "cantidad": 1
    }
  ]
}
```

**Response (201):**
```json
{
  "uuid_local": "uuid-reserva-001",
  "reserva_id": 2001,
  "codigo_reserva": "RES-uuid001",
  "estado": "CONFIRMADA"
}
```
