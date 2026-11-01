"""Endpoints de CU04 — Gestionar planes SaaS.

Acceso: SUPERADMIN únicamente.

Operaciones:
1. GET /planes — Listar planes
2. GET /planes/{plan_id} — Obtener plan
3. POST /planes — Crear plan
4. PUT /planes/{plan_id} — Actualizar plan
5. PATCH /planes/{plan_id}/estado — Cambiar estado
6. DELETE /planes/{plan_id} — Eliminar plan
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import (
    PlanCrear,
    PlanActualizar,
    PlanResponse,
    PlanListResponse,
    CambiarEstadoPlanRequest,
)
from .service import (
    PlanesService,
    PlanNombreDuplicadoError,
    PlanSlugDuplicadoError,
    PlanNoEncontradoError,
    PlanTieneSubscripcionesError,
    DatosInvalidosError,
)

router = APIRouter(prefix="/planes", tags=["CU04 - Gestionar planes SaaS"])

require_superadmin = require_roles(RolUsuario.SUPERADMIN)


@router.get("/activos", response_model=list[PlanListResponse])
def listar_planes_activos(
    db: Session = Depends(get_db),
) -> list[PlanListResponse]:
    """Listar planes activos disponibles para registro.

    Endpoint público (sin autenticación).
    Solo devuelve planes con is_active = True.
    Utilizado durante el registro de nueva empresa para seleccionar plan inicial.
    """
    service = PlanesService(db)
    planes = service.listar(is_active=True)
    return [
        PlanListResponse(
            id=p.id,
            nombre=p.nombre,
            slug=p.slug,
            descripcion=p.descripcion,
            precio=p.precio,
            limite_sucursales=p.limite_sucursales,
            limite_usuarios=p.limite_usuarios,
            gestion_productos=p.gestion_productos,
            gestion_ventas=p.gestion_ventas,
            reservas=p.reservas,
            operacion_offline=p.operacion_offline,
            reportes_convencionales=p.reportes_convencionales,
            reportes_generativos_ia=p.reportes_generativos_ia,
            es_activo=p.is_active,
        )
        for p in planes
    ]


@router.get("", response_model=list[PlanListResponse])
def listar_planes(
    estado: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> list[PlanListResponse]:
    """Listar planes disponibles.

    Query parameters:
    - estado: "activos" o "inactivos" (opcional)

    Responses:
    - **200**: Lista de planes.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    """
    is_active = None
    if estado == "activos":
        is_active = True
    elif estado == "inactivos":
        is_active = False

    service = PlanesService(db)
    planes = service.listar(is_active=is_active)
    return [
        PlanListResponse(
            id=p.id,
            nombre=p.nombre,
            slug=p.slug,
            descripcion=p.descripcion,
            precio=p.precio,
            limite_sucursales=p.limite_sucursales,
            limite_usuarios=p.limite_usuarios,
            gestion_productos=p.gestion_productos,
            gestion_ventas=p.gestion_ventas,
            reservas=p.reservas,
            operacion_offline=p.operacion_offline,
            reportes_convencionales=p.reportes_convencionales,
            reportes_generativos_ia=p.reportes_generativos_ia,
            es_activo=p.is_active,
        )
        for p in planes
    ]


@router.get("/{plan_id}", response_model=PlanResponse)
def obtener_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> PlanResponse:
    """Obtener detalles de un plan.

    Path parameters:
    - plan_id: ID del plan

    Responses:
    - **200**: Detalles del plan.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **404**: Plan no encontrado.
    """
    try:
        service = PlanesService(db)
        plan = service.obtener(plan_id)
        return PlanResponse.model_validate(plan)
    except PlanNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado.") from exc


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def crear_plan(
    payload: PlanCrear,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> PlanResponse:
    """Crear nuevo plan.

    Request body: PlanCrear

    Responses:
    - **201**: Plan creado.
    - **400**: Datos inválidos.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **409**: Nombre o slug duplicado.
    """
    try:
        service = PlanesService(db)
        plan = service.crear(payload)
        return PlanResponse.model_validate(plan)
    except PlanNombreDuplicadoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un plan con ese nombre."
        ) from exc
    except PlanSlugDuplicadoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un plan con ese slug."
        ) from exc
    except DatosInvalidosError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)
        ) from exc


@router.put("/{plan_id}", response_model=PlanResponse)
def actualizar_plan(
    plan_id: int,
    payload: PlanActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> PlanResponse:
    """Actualizar plan existente.

    Path parameters:
    - plan_id: ID del plan

    Request body: PlanActualizar

    Responses:
    - **200**: Plan actualizado.
    - **400**: Datos inválidos o plan tiene suscripciones activas.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **404**: Plan no encontrado.
    - **409**: Nombre o slug duplicado.
    """
    try:
        service = PlanesService(db)
        plan = service.actualizar(plan_id, payload)
        return PlanResponse.model_validate(plan)
    except PlanNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado.") from exc
    except PlanNombreDuplicadoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un plan con ese nombre."
        ) from exc
    except PlanSlugDuplicadoError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un plan con ese slug."
        ) from exc
    except PlanTieneSubscripcionesError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se puede modificar un plan con suscripciones activas.",
        ) from exc
    except DatosInvalidosError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)
        ) from exc


@router.patch("/{plan_id}/estado", response_model=PlanResponse)
def cambiar_estado_plan(
    plan_id: int,
    payload: CambiarEstadoPlanRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> PlanResponse:
    """Cambiar estado de un plan (activo/inactivo).

    Path parameters:
    - plan_id: ID del plan

    Request body: CambiarEstadoPlanRequest

    Responses:
    - **200**: Estado actualizado.
    - **400**: No se puede desactivar plan con suscripciones activas.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **404**: Plan no encontrado.
    """
    try:
        service = PlanesService(db)
        plan = service.cambiar_estado(plan_id, payload.is_active)
        return PlanResponse.model_validate(plan)
    except PlanNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado.") from exc
    except PlanTieneSubscripcionesError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se puede desactivar un plan con suscripciones activas.",
        ) from exc


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> None:
    """Eliminar un plan.

    Path parameters:
    - plan_id: ID del plan

    Responses:
    - **204**: Plan eliminado.
    - **400**: No se puede eliminar plan con suscripciones activas.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **404**: Plan no encontrado.
    """
    try:
        service = PlanesService(db)
        service.eliminar(plan_id)
    except PlanNoEncontradoError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado.") from exc
    except PlanTieneSubscripcionesError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se puede eliminar un plan con suscripciones activas.",
        ) from exc
