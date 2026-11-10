"""Router de CU17 -- Generar y Visualizar Reporte Dinámico.

CU17 expone su propio endpoint para solicitar reportes con filtros.
Reutiliza servicios de CU30 sin duplicación de lógica.

Responsabilidades:
1. Validar autenticación (role ADMINISTRADOR).
2. Recibir solicitud con filtros.
3. Delegar a GenerarReporteDinamicoService.
4. Retornar datos estructurados para visualización.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P7_GestionSaaSySuscripciones.CU05_GestionarSuscripcionEmpresa.service import (
    FuncionalidadNoHabilitadaError,
)

from .schemas import GenerarReporteDinamicoRequest, GenerarReporteDinamicoResponse
from .service import (
    GenerarReporteDinamicoService,
    CategoriaNoEncontradaError,
    ProductoNoEncontradoError,
)

require_administrador = require_roles(RolUsuario.ADMINISTRADOR)

router = APIRouter(
    prefix="/reportes",
    tags=["CU17 - Generar y Visualizar Reporte Dinámico"],
)


@router.post(
    "/generar-dinamico",
    response_model=GenerarReporteDinamicoResponse,
    summary="CU17 - Generar reporte dinámico con filtros",
    description="""
    Punto de entrada para CU17. Genera reportes con filtros dinámicos.

    Filtros disponibles:
    - fecha_desde/fecha_hasta: Rango de fechas (inclusivo)
    - sucursal_id: Sucursal específica (None = todas)
    - categoria_id: Categoría de producto (None = todas)
    - producto_id: Producto específico (None = todos)

    Tipos de reporte: 'completo', 'ventas', 'inventario', 'productos'

    Flow:
    1. Validar autenticación y plan SaaS
    2. Validar filtros (categoría, producto)
    3. Generar reportes via GenerarReporteDinamicoService
    4. Retornar datos estructurados para visualización
    """,
)
async def generar_reporte_dinamico(
    payload: GenerarReporteDinamicoRequest,
    actor: Usuario = Depends(require_administrador),
    db: Session = Depends(get_db),
) -> GenerarReporteDinamicoResponse:
    """Genera un reporte dinámico con filtros."""

    service = GenerarReporteDinamicoService(db)

    try:
        return service.generar_reporte(payload, actor)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )
    except FuncionalidadNoHabilitadaError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Plan sin acceso a reportes dinámicos: {str(e)}",
        )
    except (CategoriaNoEncontradaError, ProductoNoEncontradoError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generando reporte: {str(e)}",
        )
