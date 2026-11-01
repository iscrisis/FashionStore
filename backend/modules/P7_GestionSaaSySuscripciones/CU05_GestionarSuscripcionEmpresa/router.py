"""Endpoints de CU05 — Gestionar suscripción de empresa.

Acceso: SUPERADMIN únicamente.

Operaciones:
1. GET /suscripciones — Listar empresas y suscripciones
2. GET /suscripciones/{empresa_id} — Obtener suscripción de empresa
3. POST /suscripciones — Asignar plan a empresa
4. PUT /suscripciones/{empresa_id} — Cambiar plan
5. PATCH /suscripciones/{empresa_id}/renovar — Renovar suscripción
6. PATCH /suscripciones/{empresa_id}/estado — Cambiar estado
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_admin_roles, get_current_usuario
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import (
    SuscripcionCrear,
    SuscripcionResponse,
    SuscripcionConDetalleResponse,
    SuscripcionRenovar,
    SuscripcionCambiarEstado,
    ListaEmpresasSuscripciones,
)
from .service import (
    SuscripcionesService,
    EmpresaNoEncontradaError,
    PlanNoEncontradoError,
    PlanInactivoError,
    SuscripcionNoEncontradaError,
    IncompatibilidadPlanError,
)

router = APIRouter(prefix="/suscripciones", tags=["CU05 - Gestionar suscripción"])

require_superadmin = require_roles(RolUsuario.SUPERADMIN)


@router.get("", response_model=list[ListaEmpresasSuscripciones])
def listar_suscripciones(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> list[ListaEmpresasSuscripciones]:
    """Listar empresas y sus suscripciones.

    Responses:
    - **200**: Lista de empresas con suscripciones.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    """
    service = SuscripcionesService(db)
    empresas_suscripciones = service.listar_empresas_con_suscripciones()

    resultado = []
    for item in empresas_suscripciones:
        resultado.append(ListaEmpresasSuscripciones(
            id=item["empresa_id"],
            nombre=item["empresa_nombre"],
            razon_social=item["empresa_razon_social"],
            suscripcion=item["suscripcion"],
            plan=item["plan"],
        ))
    return resultado


@router.get("/{empresa_id}", response_model=SuscripcionConDetalleResponse)
def obtener_suscripcion_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> SuscripcionConDetalleResponse:
    """Obtener suscripción de una empresa.

    Path parameters:
    - empresa_id: ID de la empresa

    Responses:
    - **200**: Detalles de la suscripción con plan y funcionalidades.
    - **401**: No autenticado.
    - **403**: No tienes permiso para consultar esta empresa.
    - **404**: Empresa no encontrada.
    """
    if actor.rol == RolUsuario.SUPERADMIN:
        # SUPERADMIN puede consultar cualquier empresa
        pass
    elif actor.empresa_id == empresa_id:
        # ADMINISTRADOR o CLIENTE puede consultar su propia empresa
        pass
    else:
        # Cualquier otro caso es 403
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "No tienes permiso para consultar esta empresa."
        )

    try:
        service = SuscripcionesService(db)
        resultado = service.obtener_suscripcion_empresa(empresa_id)
        return SuscripcionConDetalleResponse(
            suscripcion=resultado["suscripcion"],
            empresa=resultado["empresa"],
            plan=resultado["plan"],
            funcionalidades_habilitadas=resultado["funcionalidades_habilitadas"],
        )
    except EmpresaNoEncontradaError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa no encontrada.") from None


@router.post("", response_model=SuscripcionResponse, status_code=status.HTTP_201_CREATED)
def asignar_plan(
    payload: SuscripcionCrear,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> SuscripcionResponse:
    """Asignar plan a una empresa.

    Request body: SuscripcionCrear

    Responses:
    - **201**: Suscripción creada.
    - **400**: Datos inválidos.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **404**: Empresa o plan no encontrado.
    """
    try:
        service = SuscripcionesService(db)
        suscripcion = service.asignar_plan(payload)
        return SuscripcionResponse.model_validate(suscripcion)
    except EmpresaNoEncontradaError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa no encontrada.") from None
    except PlanNoEncontradoError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado.") from None
    except PlanInactivoError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El plan está inactivo.") from None


@router.put("/{empresa_id}", response_model=SuscripcionResponse)
def cambiar_plan(
    empresa_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> SuscripcionResponse:
    """Cambiar plan de una empresa.

    Path parameters:
    - empresa_id: ID de la empresa

    Request body: {"plan_id": int}

    Responses:
    - **200**: Plan actualizado.
    - **400**: Datos inválidos o cambio incompatible.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **404**: Empresa, suscripción o plan no encontrado.
    """
    try:
        if "plan_id" not in payload:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "plan_id es requerido.")

        service = SuscripcionesService(db)
        suscripcion = service.cambiar_plan(empresa_id, payload["plan_id"])
        return SuscripcionResponse.model_validate(suscripcion)
    except EmpresaNoEncontradaError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa no encontrada.") from None
    except SuscripcionNoEncontradaError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Suscripción no encontrada.") from None
    except PlanNoEncontradoError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado.") from None
    except PlanInactivoError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El plan está inactivo.") from None
    except IncompatibilidadPlanError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from None


@router.patch("/{empresa_id}/renovar", response_model=SuscripcionResponse)
def renovar_suscripcion(
    empresa_id: int,
    payload: SuscripcionRenovar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> SuscripcionResponse:
    """Renovar suscripción.

    Path parameters:
    - empresa_id: ID de la empresa

    Request body: SuscripcionRenovar

    Responses:
    - **200**: Suscripción renovada.
    - **400**: Datos inválidos.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **404**: Empresa o suscripción no encontrada.
    """
    try:
        service = SuscripcionesService(db)
        suscripcion = service.renovar_suscripcion(empresa_id, payload)
        return SuscripcionResponse.model_validate(suscripcion)
    except EmpresaNoEncontradaError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa no encontrada.") from None
    except SuscripcionNoEncontradaError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Suscripción no encontrada.") from None


@router.patch("/{empresa_id}/estado", response_model=SuscripcionResponse)
def cambiar_estado_suscripcion(
    empresa_id: int,
    payload: SuscripcionCambiarEstado,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
) -> SuscripcionResponse:
    """Cambiar estado de suscripción.

    Path parameters:
    - empresa_id: ID de la empresa

    Request body: SuscripcionCambiarEstado

    Responses:
    - **200**: Estado actualizado.
    - **400**: Datos inválidos.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **404**: Empresa o suscripción no encontrada.
    """
    try:
        service = SuscripcionesService(db)
        suscripcion = service.cambiar_estado(empresa_id, payload.activa)
        return SuscripcionResponse.model_validate(suscripcion)
    except EmpresaNoEncontradaError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa no encontrada.") from None
    except SuscripcionNoEncontradaError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Suscripción no encontrada.") from None
