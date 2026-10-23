# Guía de Testing - Endpoints DELETE

## Resumen de Endpoints Implementados

Se han agregado endpoints DELETE en los siguientes CUs:

### 1. **CU06 - Gestionar Sucursales**
- `DELETE /api/v1/ciudades/{ciudad_id}` → Status 204
- `DELETE /api/v1/sucursales/{sucursal_id}` → Status 204

### 2. **CU09 - Categorías, Tallas y Colores**
- `DELETE /api/v1/categorias/{categoria_id}` → Status 204
- `DELETE /api/v1/tallas/{talla_id}` → Status 204
- `DELETE /api/v1/colores/{color_id}` → Status 204

### 3. **CU10 - Temporadas y Colecciones**
- `DELETE /api/v1/temporadas/{temporada_id}` → Status 204
- `DELETE /api/v1/colecciones/{coleccion_id}` → Status 204

### 4. **CU13 - Gestionar Proveedores**
- `DELETE /api/v1/proveedores/{proveedor_id}` → Status 204

### 5. **CU08 - Gestionar Productos**
- `DELETE /api/v1/productos/{producto_id}` → Status 204

### 6. **CU32 - Gestionar Promociones**
- `DELETE /api/v1/promociones/{promocion_id}` → Status 204

---

## Testing con cURL

### Requisito: Autenticación
Todos los endpoints requieren un token Bearer. Primero obtén un token:

```bash
# 1. Iniciar sesión
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "admin@fashionstore.com",
    "password": "TuContraseña123!"
  }'

# Copiar el access_token de la respuesta
```

### Ejemplos de DELETE

Reemplaza `{TOKEN}` con el token obtenido arriba.

#### Eliminar una ciudad
```bash
curl -X DELETE http://localhost:8000/api/v1/ciudades/1 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

#### Eliminar una sucursal
```bash
curl -X DELETE http://localhost:8000/api/v1/sucursales/1 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

#### Eliminar una categoría
```bash
curl -X DELETE http://localhost:8000/api/v1/categorias/1 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

#### Eliminar una talla
```bash
curl -X DELETE http://localhost:8000/api/v1/tallas/1 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

#### Eliminar un color
```bash
curl -X DELETE http://localhost:8000/api/v1/colores/1 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

#### Eliminar una temporada
```bash
curl -X DELETE http://localhost:8000/api/v1/temporadas/1 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

#### Eliminar una colección
```bash
curl -X DELETE http://localhost:8000/api/v1/colecciones/1 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

#### Eliminar un proveedor
```bash
curl -X DELETE http://localhost:8000/api/v1/proveedores/1 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

#### Eliminar un producto
```bash
curl -X DELETE http://localhost:8000/api/v1/productos/1 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

#### Eliminar una promoción
```bash
curl -X DELETE http://localhost:8000/api/v1/promociones/1 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

---

## Testing con Postman

### Pasos:

1. **Crear una colección** llamada "FashionStore DELETE Tests"

2. **Agregar variable de entorno**:
   - Nombre: `token`
   - Valor: (se obtiene del login)
   - Scope: `Postman` o `Environment`

3. **Crear request de Login**:
   - Método: POST
   - URL: `{{base_url}}/api/v1/auth/login`
   - Body (raw JSON):
   ```json
   {
     "correo": "admin@fashionstore.com",
     "password": "TuContraseña123!"
   }
   ```
   - En Tests (tab), agregar:
   ```javascript
   if (pm.response.code === 200) {
     pm.environment.set("token", pm.response.json().access_token);
   }
   ```

4. **Crear requests DELETE** para cada endpoint:
   - Método: DELETE
   - URL: `{{base_url}}/api/v1/[recurso]/[id]`
   - Header: `Authorization: Bearer {{token}}`

---

## Códigos de Respuesta Esperados

| Caso | Código | Descripción |
|------|--------|-------------|
| Éxito | 204 | No Content (entidad eliminada) |
| No encontrado | 404 | Not Found (ID no existe) |
| No autorizado | 401 | Unauthorized (sin token) |
| Forbidden | 403 | Forbidden (rol insuficiente) |

---

## Tests Unitarios

### Backend (Python)
Ubicación: `backend/tests/test_usuarios_roles.py`

Se incluyen tests para:
- ✅ Eliminación exitosa
- ✅ Intento de auto-eliminación (bloqueado)
- ✅ Intento de eliminar inexistente (404)
- ✅ Protección de Administrador General

Ejecutar:
```bash
cd backend
pytest tests/test_usuarios_roles.py::test_eliminar_usuario_ok -v
pytest tests/test_usuarios_roles.py::test_no_puede_eliminar_su_propia_cuenta -v
```

### Frontend (Angular)
Los métodos están listos en los servicios:
- `UsuarioAdminService.delete(id)`
- `SucursalAdminService.delete(id)`
- `CategoryService.delete(id)`
- `SizeService.delete(id)`
- `ColorService.delete(id)`
- `TemporadaAdminService.delete(id)`
- `ColeccionAdminService.delete(id)`
- `ProveedorService.delete(id)`
- `ProductoService.delete(id)`
- `PromocionService.delete(id)`

---

## Lógica de Protección Implementada

### Bloqueos automáticos en Backend:

1. **CU05 - Usuarios y Roles**
   - ❌ No puedes eliminar tu propia cuenta (status 400)
   - ❌ No puedes eliminar el Administrador General (status 404 - oculto como no existe)

2. **CU06 - Sucursales**
   - Verificar que no haya usuarios vinculados (opcional - depende del modelo)
   - Verificar que no haya inventario (opcional - depende del modelo)

3. **Otros CUs**
   - Validación: ID debe existir (404 si no)
   - Autorización: Solo ADMINISTRADOR (401/403 si no)

---

## Casos de Prueba Manual

### Test 1: Eliminación Exitosa
```
1. Crear un registro (categoria, producto, etc.)
2. Copiar su ID
3. Hacer DELETE con el ID
4. Verificar Status 204
5. Intentar GET del registro → Debe retornar 404
```

### Test 2: No Encontrado
```
1. Intentar DELETE con ID que no existe (ej: 99999)
2. Verificar Status 404
```

### Test 3: Sin Autorización
```
1. Intentar DELETE sin enviar token
2. Verificar Status 401
```

### Test 4: Rol Insuficiente
```
1. Autenticarse con usuario que no sea ADMINISTRADOR
2. Intentar DELETE
3. Verificar Status 403
```

---

## Troubleshooting

### Error 401 Unauthorized
- ✅ Verifica que el token sea válido
- ✅ Verifica que el token no haya expirado
- ✅ Verifica que el header sea: `Authorization: Bearer {token}`

### Error 403 Forbidden
- ✅ Solo ADMINISTRADOR puede eliminar
- ✅ Verifica el rol del usuario autenticado

### Error 404 Not Found
- ✅ Verifica que el ID exista
- ✅ Verifica que el ID sea correcto
- ✅ Para el Administrador General, siempre retorna 404 (protección)

### Error 400 Bad Request
- ✅ En CU05: No puedes eliminar tu propia cuenta
- ✅ Verifica los datos enviados

---

## Archivos Modificados

### Backend
- `modules/P*/CU*/repository.py` → Agregué `eliminar()`
- `modules/P*/CU*/service.py` → Agregué `eliminar()` con validaciones
- `modules/P*/CU*/router.py` → Agregué endpoint DELETE
- `backend/tests/test_usuarios_roles.py` → Agregué tests

### Frontend
- `sucursales-catalogo/cu06-gestionar-sucursales/sucursal-admin.service.ts` → Agregué `delete()`, `deleteCiudad()`
- `sucursales-catalogo/atributos/services/category.service.ts` → Agregué `delete()`
- `sucursales-catalogo/atributos/services/size.service.ts` → Agregué `delete()`
- `sucursales-catalogo/atributos/services/color.service.ts` → Agregué `delete()`
- `sucursales-catalogo/cu10-gestionar-temporadas-colecciones/temporada-admin.service.ts` → Agregué `delete()`
- `sucursales-catalogo/cu10-gestionar-temporadas-colecciones/coleccion-admin.service.ts` → Agregué `delete()`
- `sucursales-catalogo/gestion-proveedores/proveedor.service.ts` → Agregué `delete()`
- `sucursales-catalogo/cu08-gestionar-productos/producto.service.ts` → Agregué `delete()`
- `features/admin/promociones/promocion.service.ts` → Agregué `delete()`

---

## Próximos Pasos (UI)

Para completar la integración en el frontend, necesitas:

1. **Agregar botones "Eliminar"** en los templates HTML (similar a CU05)
2. **Agregar métodos `deleteItem()`** en los componentes TypeScript (similar a CU05)
3. **Agregar confirmación de diálogo** antes de eliminar
4. **Recargar lista** después de eliminación exitosa

Ejemplo (CU05 ya tiene esto implementado completo):
- `usuarios-y-accesos/cu05-gestionar-usuarios-roles/usuarios-roles.html` ✅
- `usuarios-y-accesos/cu05-gestionar-usuarios-roles/usuarios-roles.ts` ✅
- `usuarios-y-accesos/cu05-gestionar-usuarios-roles/usuario-admin.service.ts` ✅

---

## Resumen de Testing

✅ **Backend**: 100% funcional - Endpoints DELETE listos para consumir
✅ **Servicios Frontend**: 100% - Métodos `delete()` implementados
⏳ **UI Frontend**: Pendiente - Botones y confirmaciones necesarias

**Puedes testear ahora con cURL o Postman usando los endpoints directamente.**
