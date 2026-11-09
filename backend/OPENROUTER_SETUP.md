# OpenRouter Integration en CU16/CU30

## 📋 Resumen de Cambios

### Archivos Modificados

1. **app/core/config.py**
   - Agregadas variables: `IA_PROVIDER`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL`
   - Por defecto: `IA_PROVIDER=gemini` (retrocompatible)

2. **backend/.env.example**
   - Agregadas las nuevas variables de OpenRouter
   - Incluye instrucciones de configuración

3. **CU30_ConsultarReportesIndicadores/gemini_client.py**
   - Actualizadas funciones: `interpretar_consulta_reporte()`, `generar_resumen_reporte()`
   - Detectan automáticamente el proveedor configurado
   - Delegan a OpenRouter si `IA_PROVIDER=openrouter`

### Archivos Creados

1. **CU30_ConsultarReportesIndicadores/openrouter_client.py** (126 líneas)
   - Nuevo módulo que implementa cliente OpenRouter
   - Compatible con OpenAI API (`/chat/completions`)
   - Soporta reintentos con timeout de 30 segundos
   - Mismo manejo de errores que Gemini

## 🔧 Configuración

### Opción 1: Usar OpenRouter (Modelos Gratuitos, SIN Tarjeta)

1. Crear cuenta gratuita en https://openrouter.ai/

2. Copiar API Key de https://openrouter.ai/keys

3. Actualizar `backend/.env`:
```env
IA_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-tu-clave-completa-aqui
OPENROUTER_MODEL=openrouter/free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

4. Reconstruir Docker:
```bash
cd backend
docker compose build backend
docker compose up -d --no-deps --force-recreate backend
```

### Opción 2: Mantener Gemini (Por Defecto)

```env
IA_PROVIDER=gemini
GEMINI_API_KEY=tu-clave-de-gemini-aqui
GEMINI_MODEL=gemini-3.7-flash
```

### Opción 3: Cambiar entre Proveedores en Runtime

Solo cambiar `IA_PROVIDER` en `backend/.env` y reiniciar:

```bash
docker compose restart backend
```

## ✅ Pruebas

### Test Automatizado (Sin API Key Real)

```bash
cd FashionStore
python backend/test_openrouter_integration.py
```

Verifica:
- ✅ Configuración se carga correctamente
- ✅ Prompts se formatean bien
- ✅ JSON se parsea correctamente
- ✅ Provider se detecta automáticamente
- ✅ Errores mapean a fallback

### Test Real con OpenRouter (Requiere API Key)

1. Agregar API Key en `backend/.env`

2. Iniciar backend:
```bash
docker compose up -d backend
```

3. Hacer solicitud POST desde Angular o curl:

```bash
curl -X POST http://localhost:8000/api/v1/reportes/consulta-inteligente \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "consulta": "Ventas de este mes",
    "sucursal_id_actual": null,
    "fecha_desde_actual": "2026-11-01",
    "fecha_hasta_actual": "2026-11-09"
  }'
```

**Respuesta esperada** (HTTP 200):
```json
{
  "exito": true,
  "intencion": "ventas",
  "filtros": {
    "sucursal_id": null,
    "sucursal_nombre": null,
    "fecha_desde": "2026-11-01",
    "fecha_hasta": "2026-11-09"
  },
  "resumen": "[Resumen generado por OpenRouter]",
  "datos": {
    "ingresos_totales": 50000.0,
    "ventas_totales": 150,
    ...
  }
}
```

4. En Angular: Navegar a Dashboard → Admin → Reportes → Input "Ventas de este mes" → Botón GENERAR

## 🔍 Logging

En `backend/logs/` se registra el proveedor utilizado:

```log
[CU30/OpenRouter] Intento 1 realizado...
[CU30/OpenRouter] Respuesta exitosa: ventas
```

O con Gemini:
```log
[CU16/CU30] Gemini interpretación completada
```

## ⚙️ Detalles Técnicos

### Timeouts

- **OpenRouter**: 30 segundos por intento, máximo 2 intentos = 60 segundos
- **Gemini**: 30 segundos por intento, máximo 2 intentos = 60 segundos

### Modelos Soportados en OpenRouter (Gratuitos)

- `openrouter/free` (defecto) - Rota entre Llama 3, Mistral, etc.
- `meta-llama/llama-3-70b-instruct:free`
- `mistralai/mistral-7b-instruct:free`

### Otros Modelos (Requieren Créditos)

Cambiar `OPENROUTER_MODEL` en `.env`:
```env
OPENROUTER_MODEL=gpt-4o-mini
# o
OPENROUTER_MODEL=claude-3-haiku
```

## 🚨 Restricciones y Seguridad

### ✅ Garantizado

- **Sin SQL Arbitrario**: OpenRouter solo interpreta intención y filtros
- **FastAPI Valida**: Todos los parámetros se validan en backend
- **Sin Consultas Nuevas**: Reutiliza Services existentes (primera parte de CU30)
- **Timeouts**: Evita bloqueos indefinidos
- **API Key Segura**: Nunca se expone a Angular, nunca en logs

### ❌ NO Permitido

```python
# ❌ NUNCA esto:
generar_consulta_inteligente("DELETE FROM usuarios WHERE id=1")
# OpenRouter devuelve: {"intencion": null, ...}
# FastAPI rechaza: intencion no reconocida

# ✅ SIEMPRE esto:
generar_consulta_inteligente("Ventas de este mes")
# OpenRouter devuelve: {"intencion": "ventas", ...}
# FastAPI ejecuta: reportes.ventas(desde, hasta, sucursal_id)
```

## 📊 Diagnóstico

### Si la respuesta es "La consulta inteligente no está disponible":

1. Revisar logs del backend:
```bash
docker compose logs backend | grep -i openrouter
```

2. Verificar configuración:
```bash
grep -E "IA_PROVIDER|OPENROUTER" backend/.env
```

3. Si el error es 401: API Key inválida o expirada

4. Si el error es 429: Rate limit excedido (esperar o cambiar a créditos)

5. Si el error es 500: OpenRouter con problemas (fallback a Gemini o esperar)

## 🔄 Cambiar de Proveedor

**De Gemini a OpenRouter:**
```env
IA_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
```

**De OpenRouter a Gemini:**
```env
IA_PROVIDER=gemini
GEMINI_API_KEY=...
```

**Reiniciar:**
```bash
docker compose restart backend
```

## 📝 Notas

- OpenRouter es **100% compatible con el contrato de respuesta** de Gemini
- **Sin cambios en Angular**: funciona igual con cualquier proveedor
- **Sin cambios en PostgreSQL**: los Services de reportes son idénticos
- **Retrocompatible**: por defecto usa Gemini (como antes)

## 🎯 Próximos Pasos

1. Crear API Key en OpenRouter (sin tarjeta)
2. Actualizar `backend/.env`
3. Hacer `docker compose up -d --no-deps --force-recreate backend`
4. Probar desde Angular: Dashboard → Reportes → Input → GENERAR
5. Verificar logs: `docker compose logs backend | grep CU30`

---

**Creado**: 2026-11-09
**Proveedor por defecto**: Gemini (retrocompatible)
**Proveedor alternativo**: OpenRouter (gratuito, sin tarjeta)
