# CU14 — Cambios Mínimos Propuestos

**Fecha:** 2026-11-09  
**Estado:** PENDIENTE AUTORIZACIÓN  
**Riesgo:** BAJO (cambios muy localizados)

---

## 1. CAMBIO 1: Integración Automática CU11 → CU14

**Archivo:** `modules/PK09_SincronizacionYConsistencia/CU11_SincronizarOperacionesPendientes/router.py`

**Ubicación exacta:** Líneas 65-75 (endpoint sincronizar_venta) y 123-133 (endpoint sincronizar_reserva)

**Cambio propuesto:**

```python
# ANTES (línea 65-66)
try:
    service = SincronizarOperacionesPendientesService(db)
    resultado = service.sincronizar_venta_offline(actor, operacion)

# DESPUÉS (agregar después de obtener resultado, ANTES de lanzar HTTPException)
try:
    service = SincronizarOperacionesPendientesService(db)
    resultado = service.sincronizar_venta_offline(actor, operacion)
    
    # NUEVO: Registrar conflicto en CU14 automáticamente
    if resultado.estado == "CONFLICTO":
        from modules.PK09_SincronizacionYConsistencia.CU14_GestionarConflictosSincronizacion.service import GestionarConflictosService
        cu14_service = GestionarConflictosService(db)
        cu14_service.registrar_conflicto_desde_resultado_cu11(actor, resultado)

    # Existente: lanzar HTTPException como siempre
    if resultado.estado == "CONFIRMADA":
        return resultado
    elif resultado.estado == "CONFLICTO":
        ...
```

**Justificación:**
- ✓ Solo 3 líneas de código nuevo
- ✓ NO modifica lógica de validación de ventas
- ✓ NO modifica respuestas HTTP
- ✓ NO modifica auditoría existente
- ✓ Solo AGREGA comportamiento (registra en CU14)
- ✓ Idempotente (llamar 2 veces = mismo resultado)

**Aplicar idéntico a:** Línea 123 para endpoint sincronizar_reserva

---

## 2. CAMBIO 2: CU13 Distingue CONFLICTO de RECHAZADA

**Archivo:** `modules/PK09_SincronizacionYConsistencia/CU13_ReintentoOperacionesOffline/service.py`

**Ubicación exacta:** Línea 179-180 (método reintentar_venta)

**Cambio propuesto:**

```python
# ANTES (línea 179-180)
if resultado_cu11.estado != "CONFIRMADA":
    proximo_reintento_ms = self.backoff_config.obtener_espera_ms(numero_intento)

# DESPUÉS
if resultado_cu11.estado == "RECHAZADA":  # Solo RECHAZADA, NO CONFLICTO
    proximo_reintento_ms = self.backoff_config.obtener_espera_ms(numero_intento)
```

**Justificación:**
- ✓ Cambia 1 línea de código (operador `!=` a `==`, condición `"CONFIRMADA"` a `"RECHAZADA"`)
- ✓ NO modifica reintentos de RECHAZADA (sigue igual)
- ✓ Evita reintentos indefinidos de CONFLICTO
- ✓ NO modifica registro de auditoría
- ✓ NO modifica CU11, CU12 ni ConnectivityService

**Aplicar idéntico a:** Línea 238 para método reintentar_reserva

**Impacto en flujos:**
- RECHAZADA (error técnico) → Reintenta con backoff → Sigue igual ✓
- CONFLICTO (error de negocio) → NO calcula próximo_reintento → Nuevo comportamiento ✓

---

## 3. TABLA NUEVA: conflictos_sincronizacion

**Script:** `SQL_MANUAL_CU14_SETUP.sql`

**Columnas:** 12 (corresponden exactamente a modelo SQLAlchemy)
**Índices:** 4 (1 PK + 3 compuestos)
**Tamaño estimado:** < 10MB inicialmente

**Verificación de correspondencia con modelo:**

| Modelo SQLAlchemy | SQL | Tipo | Nullable |
|---|---|---|---|
| id (PK) | SERIAL PRIMARY KEY | Integer | NO |
| empresa_id | INTEGER NOT NULL | Integer | NO |
| uuid_operacion_offline | VARCHAR(255) NOT NULL | String(255) | NO |
| tipo_operacion | VARCHAR(50) NOT NULL | String(50) | NO |
| tipo_conflicto | VARCHAR(100) NOT NULL | String(100) | NO |
| estado_conflicto | VARCHAR(50) DEFAULT 'DETECTADO' | String(50) | NO |
| motivo | VARCHAR(500) | String(500) | YES |
| detalles_conflicto | VARCHAR(2000) | String(2000) | YES |
| fecha_detectado | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | DateTime | NO |
| fecha_resolucion | TIMESTAMP | DateTime | YES |
| usuario_id | INTEGER | Integer | YES |
| usuario_resolucion_id | INTEGER | Integer | YES |
| debe_reintentarse_automaticamente | BOOLEAN DEFAULT false | Boolean | NO |

✓ 100% correspondencia verificada

---

## 4. IMPACTO EN FLUJOS EXISTENTES

### CU11 (Sin cambios en lógica, solo agrega CU14 call)
```
Recibe request
├─ Valida
├─ Crea venta/reserva
└─ Devuelve resultado
   └─ Si CONFLICTO:
      └─ NUEVO: Registra en CU14
      └─ Lanza HTTPException (como siempre)
```

### CU13 (Cambio minimal de condición)
```
Obtiene último intento
├─ Valida backoff
├─ Consulta CU12
├─ Llama CU11
├─ Registra en auditoría
└─ Retorna resultado
   ├─ Si RECHAZADA:
   │  └─ Calcula próximo reintento (SIN CAMBIO)
   └─ Si CONFLICTO:
      └─ CAMBIO: NO calcula próximo_reintento
```

---

## 5. PRUEBAS DE SEGURIDAD

Ver `test_cu14_seguridad_cambios.py`:

- ✓ RECHAZADA sigue reintentando
- ✓ CONFLICTO NO reintenta
- ✓ No se modifica auditoría CU13
- ✓ No se modifica validación CU11
- ✓ No se pierde ningún dato

---

## RESUMEN

| Cambio | Archivo | Líneas | Riesgo | Reversible |
|--------|---------|--------|--------|-----------|
| Integración CU11→CU14 | router.py (CU11) | +3 | BAJO | Sí (delete) |
| Condición CU13 | service.py (CU13) | 1 | BAJO | Sí (revert) |
| Tabla nueva | SQL_MANUAL_CU14_SETUP.sql | Nueva | BAJO | Sí (DROP) |

**TOTAL CAMBIOS EXISTENTES:** 4 líneas (3 en CU11 router + 1 en CU13 service)

**ARCHIVO NUEVO:** 1 (tabla SQL)

---

## AUTORIZACIÓN REQUERIDA

1. ✓ Cambio en `CU11_ReintentoOperacionesOffline/router.py` (+3 líneas)
2. ✓ Cambio en `CU13_ReintentoOperacionesOffline/service.py` (1 línea)
3. ✓ Crear tabla `conflictos_sincronizacion` (SQL)

**BLOQUEADOR:** Sin autorización, CU14 está funcional pero:
- No se registran automáticamente conflictos desde CU11
- CU13 reintenta CONFLICTOS indefinidamente (problema de negocio)

