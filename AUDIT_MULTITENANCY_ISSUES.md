# AUDITORÍA REAL: PROBLEMAS DE MULTITENANCY EN P1

**Fecha**: 2026-11-01  
**Estado**: CRÍTICO - Se confirmaron dos problemas graves

---

## 1. ESTADO DE LA BD ✓ CORRECTO

```
FashionStore (id=2): PROFESIONAL, reportes_generativos_ia = true
TestCorp    (id=3): PROFESIONAL, reportes_generativos_ia = true  
SHEIN       (id=4): BÁSICO,       reportes_generativos_ia = false
```

Todas las entidades tienen columna `empresa_id`:
- ✓ categorias
- ✓ productos
- ✓ proveedores
- ✓ temporadas
- ✓ colecciones

Registros en BD:
- FashionStore: 3 categorías, 1 producto, 1 proveedor, 1 temporada, 1 colección
- SHEIN: 0 registros (correcto)

---

## 2. PROBLEMA 1: MULTITENANCY ROTO ❌

### CU08 - Gestionar Productos (CRÍTICO)

**Archivo afectado**: `CU08_GestionarProductos/router.py:55-73`

```python
@router.get("", response_model=list[ProductoOut])
def listar_productos(
    search: str | None = Query(default=None),
    ...
    _: Usuario = Depends(require_admin),  # ← El usuario se descarta con _
) -> list[ProductoOut]:
    return ProductosService(db).listar(
        search=search,
        # ← NO SE PASA empresa_id
        # ← NO SE PASA usuario
    )
```

**Problema en repository**: `CU08_GestionarProductos/repository.py:30-53`

```python
def listar(
    self,
    search: str | None = None,
    categoria_id: int | None = None,
    # ← NO TIENE PARÁMETRO empresa_id
) -> list[Producto]:
    stmt = select(Producto)
    if search:
        stmt = stmt.where(func.lower(Producto.nombre).like(...))
    # ← NUNCA FILTRA POR empresa_id
    return list(self.db.execute(stmt).scalars().all())
```

**Impacto**: Cuando SHEIN hace GET /productos, obtiene TODOS los productos de todas las empresas (FashionStore, TestCorp, SHEIN).

---

### CU10 - Gestionar Temporadas/Colecciones (CRÍTICO)

**Archivo**: `CU10_GestionarTemporadasColecciones/router.py`

Similar problema: recibe usuario pero no lo pasa al service.

---

### CU09 - Gestionar Proveedores (CRÍTICO)

**Archivo**: `CU09_GestionarProveedores/` 

Mismo patrón: NO filtra por empresa_id.

---

### CU11 - Consultar Catálogo (PÚBLIC pero multitenant)

**Problema**: El catálogo público puede mostrarse a clientes de cualquier empresa, pero el administrador de una empresa debe ver solo SU catálogo.

---

## 3. PROBLEMA 2: IA GLOBAL ❌

El código frontend/backend implementado intenta proteger IA, pero hay problemas:

### Problema A: CU29 (Asistente IA)

En `CU29_ObtenerRecomendacionesIA/router.py`, la validación de capacidades es:

```python
if actor and actor.empresa_id:
    capacidades = CapacidadesEmpresa(db, actor.empresa_id)
    capacidades.validar_acceso_a("reportes_generativos_ia")
```

**PERO**: El asistente IA funciona para invitados (sin token):

```python
actor: Usuario | None = Depends(get_current_usuario_opcional)
```

**Impacto**: Si la empresa del catálogo público es SHEIN (BÁSICO), un INVITADO puede usar el asistente IA sin autenticarse.

### Problema B: CU30 (Reportes IA)

La protección está en el endpoint, pero los reportes convencionales también necesitan validación de empresa_id que NO existe en el service.

---

## 4. TABLA DE ENDPOINTS AFECTADOS

| CU | Endpoint | Endpoint Actual | Filtra empresa_id | CRÍTICO |
|----|----------|------------------|-------------------|---------|
| CU06 | GET /sucursales | ✓ Pasa usuario | ✓ Sí | No |
| CU08 | GET /productos | ✗ Descarta usuario | ✗ No | SÍ |
| CU08 | GET /productos/{id} | ✗ No valida tenant | ✗ No | SÍ |
| CU08 | POST /productos | ✓ Pasa usuario | Parcial | SÍ |
| CU09 | GET /proveedores | ✗ No pasa usuario | ✗ No | SÍ |
| CU09 | POST /propuestas | ? Requiere audit | ? | SÍ |
| CU10 | GET /temporadas | ✗ No pasa usuario | ✗ No | SÍ |
| CU10 | GET /colecciones | ✗ No pasa usuario | ✗ No | SÍ |
| CU11 | GET /catalogo (público) | Public + Admin | ? | SÍ |
| CU29 | POST /asistente-ia | ✓ Valida capacidades | N/A | SÍ (invitados sin empresa) |
| CU30 | POST /consulta-inteligente | ✓ Valida capacidades | N/A | SÍ |

---

## 5. CAUSA RAÍZ

**Por qué sucede**:

La arquitectura de P1 fue diseñada originalmente como **single-tenant** (una sola FashionStore).

Cuando se agregó SaaS (P7), las tablas se modificaron para agregar `empresa_id`, pero:

1. Los **routers** reciben el usuario autenticado pero lo **descartan** con `_`
2. Los **services** no aceptan `usuario` o `empresa_id` como parámetro
3. Los **repositories** nunca filtran por `empresa_id`
4. Las **relaciones** entre entidades NO validan que pertenecen al mismo tenant

---

## 6. VALIDACIÓN DE RELACIONES

**Ejemplo problema**: Un administrador de SHEIN podría:

```
1. Obtener categoria_id=1 (que pertenece a FashionStore, porque GET /categorias devuelve todas)
2. Crear un producto con esa categoría
3. Resultado: Producto SHEIN + Categoría FashionStore
```

Las validaciones en `CatalogoLecturaRepository` usan `self.db.get(Categoria, categoria_id)` sin validar `empresa_id`.

---

## 7. LISTA DE ARCHIVOS QUE REQUIEREN CAMBIOS

### CRÍTICOS (Multitenancy)

- [ ] `CU08_GestionarProductos/router.py` - Pasar usuario a service.listar()
- [ ] `CU08_GestionarProductos/service.py` - Aceptar usuario, pasar a repository
- [ ] `CU08_GestionarProductos/repository.py` - Filtrar por empresa_id en listar()
- [ ] `CU09_GestionarProveedores/` (router.py, service.py, repository.py) - Mismo patrón
- [ ] `CU10_GestionarTemporadasColecciones/` (router.py, service.py, repository.py) - Mismo patrón
- [ ] `CU11_ConsultarCatalogoPrendas/` - Validar tipo de request (admin vs público)
- [ ] `CU08_GestionarProductos/repository.py` - Validar tenant en get_by_id()
- [ ] `CU09_GestionarProveedores/repository.py` - Validar tenant en get_by_id()
- [ ] `CU10_GestionarTemporadasColecciones/repository.py` - Validar tenant en get_by_id()
- [ ] `CU08_GestionarProductos/repository.py` - Validar tenant en POST (crear con empresa_id del usuario)

### IMPORTANTES (IA)

- [ ] `CU29_ObtenerRecomendacionesIA/router.py` - Manejar el caso de invitados sin empresa
- [ ] `CU30_ConsultarReportesIndicadores/` - Validar empresa_id en todos los reportes convencionales

---

## 8. RELACIONES QUE REQUIEREN VALIDACIÓN

Al crear/actualizar un producto, validar que:
- `producto.categoria_id` → `categorias.empresa_id` == usuario.empresa_id
- `producto.temporada_id` → `temporadas.empresa_id` == usuario.empresa_id
- `producto.coleccion_id` → `colecciones.empresa_id` == usuario.empresa_id
- `producto.proveedor_id` → `proveedores.empresa_id` == usuario.empresa_id

---

## 9. PLAN DE CORRECCIÓN (NO EJECUTADO AÚN)

1. Modificar router de CU08 para pasar usuario
2. Modificar service de CU08 para aceptar usuario
3. Modificar repository de CU08 para filtrar por empresa_id
4. Repetir 1-3 para CU09, CU10
5. Agregar validación de relaciones en CU08 service
6. Manejar invitados en CU29
7. Validar enterprise_id en reportes convencionales de CU30
8. PROBAR con FashionStore vs SHEIN

---

## 10. ESTADO DE LOS CAMBIOS ANTERIORES

✗ **Los cambios de IA anteriores NO resolvieron multitenancy**  
✗ **Los cambios de IA NO están totalmente implementados**

Razón: No se hizo una auditoría previa para identificar que el problema es más profundo.

---

**SIGUIENTE PASO**: Esperar autorización para proceder con correcciones.
