# CU03 — Asociar Usuarios y Sucursales a Empresa

## Descripción

**CU03** implementa la lógica de multitenant/SaaS: cuando un ADMINISTRADOR crea un usuario o una sucursal, estos se **asocian automáticamente** a la empresa del administrador autenticado.

Antes de esta reorganización, la lógica estaba distribuida dentro de:
- `CU05/service.py` (asociación usuario → empresa)
- `CU06/service.py` (asociación sucursal → empresa)

Ahora, esa lógica está **centralizada en P7/CU03** como servicios compartidos que son reutilizados por CU05 y CU06.

---

## Estructura

```
CU03_AsociarUsuariosYSucursalesEmpresa/
├── __init__.py          # Documentación del módulo
├── service.py           # AsociacionesEmpresaService
├── repository.py        # AsociacionesEmpresaRepository (validaciones de tenant)
├── tests.py             # Tests unitarios
└── README.md            # Este archivo
```

**Nota**: CU03 NO tiene `router.py` porque **reutiliza los endpoints de CU05 y CU06**:
- `POST /usuarios` (CU05) — crea usuario asociado a empresa
- `POST /sucursales` (CU06) — crea sucursal asociada a empresa

---

## Componentes

### AsociacionesEmpresaService

Servicio que proporciona la lógica central de CU03:

#### Métodos públicos:

**`obtener_empresa_id_del_actor(actor: Usuario) -> int`**
- Obtiene la empresa_id del ADMINISTRADOR autenticado
- Valida que sea ADMINISTRADOR (no SUPERADMIN, no otros roles)
- Valida que tenga empresa asignada

**`validar_empresa_id(recurso_empresa_id: int, empresa_id_esperado: int) -> None`**
- Valida que un recurso pertenezca a la empresa correcta (validación de tenant)
- Lanza `TenantViolationError` si no coinciden

**`asignar_empresa_al_usuario(usuario: Usuario, empresa_id: int) -> None`**
- Asigna una empresa a un usuario durante su creación
- Operación central de CU03 para usuarios

**`asignar_empresa_a_sucursal(sucursal, empresa_id: int) -> None`**
- Asigna una empresa a una sucursal durante su creación
- Operación central de CU03 para sucursales

#### Excepciones:

- **`UsuarioSinEmpresaError`**: El usuario no tiene empresa asignada
- **`RolNoAutorizadoParaAsociacionError`**: No es ADMINISTRADOR
- **`TenantViolationError`**: Violación de aislamiento de tenant

### AsociacionesEmpresaRepository

Acceso a datos para validaciones de tenant:

**`usuario_pertenece_a_empresa(usuario_id: int, empresa_id: int) -> bool`**
- Verifica si un usuario pertenece a una empresa

**`sucursal_pertenece_a_empresa(sucursal_id: int, empresa_id: int) -> bool`**
- Verifica si una sucursal pertenece a una empresa

**`listar_usuarios_de_empresa(empresa_id: int) -> list[Usuario]`**
- Lista todos los usuarios de una empresa

**`listar_sucursales_de_empresa(empresa_id: int) -> list[Sucursal]`**
- Lista todas las sucursales de una empresa

---

## Integración con CU05

En `CU05/service.py`, el método `crear()` ahora usa CU03 para asignar empresa:

```python
# Antes:
empresa_id = None
if current_user is not None and current_user.rol == RolUsuario.ADMINISTRADOR:
    empresa_id = current_user.empresa_id

usuario = Usuario(..., empresa_id=empresa_id)

# Después:
cu03_service = AsociacionesEmpresaService(db)
empresa_id = cu03_service.obtener_empresa_id_del_actor(current_user)

usuario = Usuario(..., empresa_id=empresa_id)
```

**Beneficio**: La lógica de validación es centralizada. Si hay cambios en las reglas de CU03, se actualizan en un solo lugar.

---

## Integración con CU06

En `CU06/service.py`, el método `crear()` ahora usa CU03 para asignar empresa:

```python
# Antes:
sucursal = Sucursal(..., empresa_id=usuario.empresa_id)

# Después:
sucursal = Sucursal(...)  # Sin empresa_id aún
cu03_service = AsociacionesEmpresaService(db)
cu03_service.asignar_empresa_a_sucursal(sucursal, usuario.empresa_id)
```

**Beneficio**: La asignación es explícita y auditoria ble.

---

## Endpoints API

| Método | Ruta | Implementa | Descripción |
|---|---|---|---|
| POST | `/usuarios` | CU05 + CU03 | Crear usuario (asociado a empresa automáticamente) |
| POST | `/sucursales` | CU06 + CU03 | Crear sucursal (asociada a empresa automáticamente) |

Los endpoints se conservan exactamente igual. **No hay cambios en el contrato HTTP**.

---

## Validación de Tenant (Multitenant Isolation)

La seguridad de aislamiento de tenant se implementa en múltiples niveles:

### Nivel 1: Asignación (CU03)
Cuando se crea un usuario o sucursal, se asigna automáticamente a la empresa del actor.

```python
usuario.empresa_id = current_user.empresa_id  # Asignación forzada
```

### Nivel 2: Filtrado (Repository)
Cuando se listan usuarios/sucursales, se filtran por empresa del usuario autenticado.

```python
stmt = stmt.where(Usuario.empresa_id == current_user.empresa_id)
```

### Nivel 3: Validación (CU03)
Cuando se actualiza o se accede a un recurso, se valida que pertenezca a la empresa correcta.

```python
cu03_service.validar_empresa_id(recurso.empresa_id, expected_empresa_id)
```

---

## Tests

Ver `tests.py` para:
- Test de obtención de empresa_id
- Test de validación de roles
- Test de validación de tenant
- Test de asignación a usuario
- Test de asignación a sucursal

**Ejecución**:
```bash
pytest modules/P7_GestionSaaSySuscripciones/CU03_AsociarUsuariosYSucursalesEmpresa/tests.py
```

---

## Notas de Implementación

### ¿Por qué CU03 no es un paquete con router propio?

1. **Reutilización**: Los endpoints ya existen en CU05 y CU06. No duplicar.
2. **Simplicidad**: Evita confusión arquitectónica (¿cuál es el endpoint de CU03?).
3. **Mantenibilidad**: Un único punto de entrada (`POST /usuarios`, `POST /sucursales`).
4. **Contrato API**: Sin cambios — los clientes (frontend) no necesitan actualizar.

### ¿Cómo sé que CU03 está en P7 y no en P2?

CU03 es **funcionalidad de P2** (el segundo parcial), pero se ubica en **P7 (Gestión SaaS)** porque:
- Es un servicio **compartido** entre múltiples CU
- Es **fundamental para el modelo multitenant**
- Debe estar en la capa de **infraestructura SaaS**, no en módulos de negocio

---

## Línea de Tiempo

| Fecha | Evento |
|---|---|
| 2026-10-31 | Creación de CU03 como módulo centralizado en P7 |
| 2026-10-31 | Actualización de CU05 para reutilizar CU03 |
| 2026-10-31 | Actualización de CU06 para reutilizar CU03 |
| 2026-10-31 | Creación de tests de CU03 |
| 2026-10-31 | Reorganización completada sin cambios de API |

---

## Migración desde la Estructura Anterior

**Para desarrolladores que trabajaban con CU05/CU06:**

1. El comportamiento es **exactamente igual** — sin cambios funcionales
2. Los endpoints son **idénticos** — mismas rutas, mismos parámetros
3. La lógica ahora está **centralizada** en CU03 — mantenimiento más fácil
4. Importar CU03 si necesitas validaciones de tenant explícitas

**Ejemplo de uso de CU03 en otro módulo:**

```python
from modules.P7_GestionSaaSySuscripciones.CU03_AsociarUsuariosYSucursalesEmpresa.service import (
    AsociacionesEmpresaService,
)

db: Session  # tu sesión
user: Usuario  # usuario autenticado

service = AsociacionesEmpresaService(db)
empresa_id = service.obtener_empresa_id_del_actor(user)
```

---

**Fin del documento**
