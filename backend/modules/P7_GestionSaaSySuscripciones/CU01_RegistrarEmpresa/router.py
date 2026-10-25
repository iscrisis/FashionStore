"""Endpoints de CU01 — Registrar empresa contratante.

Este endpoint permite registrar una nueva empresa con su administrador inicial.
La operación es atómica: si falla la creación del administrador, se hace rollback
de la empresa.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from .schemas import EmpresaCrear, RegistroEmpresaOut
from .service import (
    EmpresasService,
    EmpresaNombreDuplicadoError,
    EmpresaSlugDuplicadoError,
    CorreoAdministradorDuplicadoError,
)

router = APIRouter(prefix="/empresas", tags=["CU01 - Registrar Empresa"])


@router.post(
    "",
    response_model=RegistroEmpresaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar empresa contratante",
    description="Crea una nueva empresa/tenant con su administrador inicial en la plataforma SaaS.",
)
def registrar_empresa(
    datos: EmpresaCrear,
    db: Session = Depends(get_db),
) -> RegistroEmpresaOut:
    """Registrar una nueva empresa contratante con administrador.

    ### Request
    **Datos de la empresa:**
    - `nombre`: Nombre de la empresa (2-150 caracteres, único)
    - `slug`: Identificador URL (2-100 caracteres, único, minúsculas)
    - `razon_social`: Razón social registrada (2-200 caracteres)
    - `correo`: Email de contacto válido
    - `telefono`: Teléfono de contacto (6-30 caracteres)

    **Datos del administrador:**
    - `nombre_admin`: Nombre completo del administrador (mínimo 2 caracteres)
    - `correo_admin`: Email del administrador (único)
    - `password`: Contraseña (mínimo 6 caracteres)

    ### Responses
    - **201**: Empresa + Administrador creados exitosamente.
    - **400**: Validación fallida (campos inválidos, formato incorrecto).
    - **409**: Conflicto - nombre, slug o correo duplicado.

    ### Ejemplo de request
    ```json
    {
        "nombre": "FashionCo SA",
        "slug": "fashionco-sa",
        "razon_social": "FashionCo Sociedad Anónima",
        "correo": "contacto@fashionco.com",
        "telefono": "+591 2 1234567",
        "nombre_admin": "Juan Pérez",
        "correo_admin": "juan@fashionco.com",
        "password": "MiContraseñaSegura123"
    }
    ```

    ### Ejemplo de response (201)
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
            "created_at": "2026-10-24T10:30:00+00:00"
        }
    }
    ```
    """
    try:
        service = EmpresasService(db)
        resultado = service.crear(datos)
        return resultado
    except EmpresaNombreDuplicadoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una empresa con ese nombre.",
        )
    except EmpresaSlugDuplicadoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una empresa con ese slug.",
        )
    except CorreoAdministradorDuplicadoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo de administrador.",
        )
