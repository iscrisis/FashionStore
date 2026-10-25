"""Endpoints de CU02 — Gestionar administrador de empresa.

Acceso: SUPERADMIN únicamente.

Operaciones:
1. GET /empresas/{empresa_id}/administrador - Consultar administrador
2. PUT /empresas/{empresa_id}/administrador - Actualizar administrador
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario, require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario

from .schemas import (
    AdministradorActualizar,
    ConsultarAdministradorOut,
)
from .service import (
    AdministradorEmpresaService,
    EmpresaNoEncontradaError,
    AdministradorNoEncontradoError,
    AdministradorTieneOtroRolError,
    CorreoDuplicadoError,
    TenantViolationError,
)

router = APIRouter(
    prefix="/empresas",
    tags=["CU02 - Gestionar Administrador de Empresa"],
)


@router.get(
    "/{empresa_id}/administrador",
    response_model=ConsultarAdministradorOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar administrador de empresa",
    description="Obtiene los datos del administrador asociado a una empresa. Solo SUPERADMIN.",
)
def consultar_administrador(
    empresa_id: int,
    _: Usuario = Depends(require_roles(RolUsuario.SUPERADMIN)),
    db: Session = Depends(get_db),
) -> ConsultarAdministradorOut:
    """Consultar administrador de una empresa específica.

    ### Parámetros
    - `empresa_id` (path): ID de la empresa

    ### Responses
    - **200**: Datos de empresa + administrador.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **404**: Empresa o administrador no encontrados.

    ### Ejemplo de response (200)
    ```json
    {
        "empresa": {
            "id": 2,
            "nombre": "FashionCo SA",
            "slug": "fashionco-sa",
            "razon_social": "FashionCo Sociedad Anónima",
            "correo": "contacto@fashionco.com",
            "telefono": "+591 2 1234567",
            "is_active": true,
            "created_at": "2026-10-24T10:30:00+00:00",
            "updated_at": "2026-10-24T10:30:00+00:00"
        },
        "administrador": {
            "id": 5,
            "nombre": "Juan Pérez",
            "correo": "juan@fashionco.com",
            "rol": "ADMINISTRADOR",
            "is_active": true,
            "empresa_id": 2,
            "created_at": "2026-10-24T10:30:00+00:00"
        }
    }
    ```
    """
    try:
        service = AdministradorEmpresaService(db)
        return service.consultar_administrador(empresa_id)
    except EmpresaNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La empresa no existe.",
        )
    except AdministradorNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe administrador asociado a esta empresa.",
        )
    except AdministradorTieneOtroRolError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inconsistencia de datos: el usuario encontrado no es ADMINISTRADOR.",
        )


@router.put(
    "/{empresa_id}/administrador",
    response_model=ConsultarAdministradorOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar datos del administrador",
    description="Actualiza nombre, correo y estado del administrador. Solo SUPERADMIN.",
)
def actualizar_administrador(
    empresa_id: int,
    datos: AdministradorActualizar,
    _: Usuario = Depends(require_roles(RolUsuario.SUPERADMIN)),
    db: Session = Depends(get_db),
) -> ConsultarAdministradorOut:
    """Actualizar datos del administrador de una empresa.

    ### Request
    - `nombre`: Nuevo nombre del administrador
    - `correo`: Nuevo correo (único en el sistema)
    - `is_active`: Estado (activo/inactivo)

    IMPORTANTE: No es posible cambiar:
    - El rol (siempre ADMINISTRADOR)
    - La empresa asociada

    ### Responses
    - **200**: Administrador actualizado exitosamente.
    - **400**: Validación fallida.
    - **401**: No autenticado.
    - **403**: No es SUPERADMIN.
    - **404**: Empresa o administrador no encontrados.
    - **409**: Correo duplicado.

    ### Ejemplo de request
    ```json
    {
        "nombre": "Juan Carlos Pérez",
        "correo": "juan.perez@fashionco.com",
        "is_active": true
    }
    ```
    """
    try:
        service = AdministradorEmpresaService(db)
        return service.actualizar_administrador(empresa_id, datos)
    except EmpresaNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La empresa no existe.",
        )
    except AdministradorNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe administrador asociado a esta empresa.",
        )
    except CorreoDuplicadoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe otro usuario con ese correo.",
        )
    except TenantViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Violación de aislamiento de tenants. No se puede cambiar la empresa asociada.",
        )
    except AdministradorTieneOtroRolError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inconsistencia de datos: el usuario encontrado no es ADMINISTRADOR.",
        )
