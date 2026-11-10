"""Router de CU18 -- Exportar Reporte Generado.

CU18 expone endpoint para descargar reportes dinámicos en PDF o Excel.
Reutiliza CU17 para generar datos y CU30 para consultas.

Responsabilidades:
1. Validar autenticación (role ADMINISTRADOR).
2. Recibir solicitud con filtros y formato.
3. Delegar a ExportarReporteService.
4. Retornar archivo descargable.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P7_GestionSaaSySuscripciones.CU05_GestionarSuscripcionEmpresa.service import (
    FuncionalidadNoHabilitadaError,
)

from .schemas import ExportarReporteRequest
from .service import ExportarReporteService

logger = logging.getLogger(__name__)

require_administrador = require_roles(RolUsuario.ADMINISTRADOR)

router = APIRouter(
    prefix="/reportes",
    tags=["CU18 - Exportar Reporte Generado"],
)


@router.post(
    "/exportar",
    summary="CU18 - Exportar reporte dinámico a PDF o Excel",
    description="""
    Exporta un reporte dinámico a PDF o Excel.

    Formato: 'pdf' o 'xlsx'
    Filtros: igual que CU17 (fecha, sucursal, categoría, producto)
    Tipo: 'completo', 'ventas', 'inventario', 'productos'

    Flow:
    1. Validar autenticación y plan SaaS
    2. Generar datos via CU17
    3. Formatear en PDF o Excel
    4. Retornar archivo descargable
    """,
)
async def exportar_reporte(
    payload: ExportarReporteRequest,
    actor: Usuario = Depends(require_administrador),
    db: Session = Depends(get_db),
):
    """Exporta un reporte dinámico."""

    service = ExportarReporteService(db)

    try:
        contenido, nombre_archivo = service.exportar(payload, actor)

        # Determinar MIME type según formato
        mime_type = (
            "application/pdf"
            if payload.formato.lower() == "pdf"
            else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        logger.info(
            f"[CU18] Archivo descargado: {nombre_archivo}, "
            f"Tamaño: {len(contenido)} bytes, Usuario: {actor.id}"
        )

        return StreamingResponse(
            iter([contenido]),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={nombre_archivo}"
            },
        )

    except ValueError as e:
        logger.error(f"[CU18] Error de validación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )
    except FuncionalidadNoHabilitadaError as e:
        logger.warning(f"[CU18] Funcionalidad no habilitada: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Plan sin acceso a reportes dinámicos: {str(e)}",
        )
    except Exception as e:
        logger.error(f"[CU18] Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error exportando reporte: {str(e)}",
        )
