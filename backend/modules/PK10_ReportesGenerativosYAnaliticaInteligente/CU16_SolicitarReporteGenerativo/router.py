"""Router de CU16 -- Integración sin duplicación de endpoints.

CU16 NO crea un endpoint nuevo. En su lugar, reutiliza completamente
el endpoint existente de CU30 (POST /reportes/consulta-inteligente).

La diferencia entre CU16 y CU30 es responsabilidad, no infraestructura:
- CU30: Consulta inteligente de reportes (backend puro)
- CU16: Solicitud de reporte generativo (orquestación con validación SaaS)

Ambas apuntan al mismo endpoint. La lógica de discriminación
(si es CU16 o CU30) ocurre en la capa de servicio/negocio.

Esto evita duplicación de API y mantiene el contrato limpio.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P6_InnovacionYAnalisis.CU30_ConsultarReportesIndicadores.schemas import (
    ConsultaInteligenteRequest,
    ConsultaInteligenteResponse,
)

from .service import SolicitarReporteGenerativoService

require_administrador = require_roles(RolUsuario.ADMINISTRADOR)

router = APIRouter(
    prefix="/reportes",
    tags=["CU16 - Solicitar Reporte Generativo"],
)


@router.post(
    "/solicitar-generativo",
    response_model=ConsultaInteligenteResponse,
    summary="CU16 - Solicitar reporte generativo (texto/voz)",
    description="""
    Punto de entrada para CU16. Reutiliza el servicio de CU30.

    Endpoint separado para claridad de intención, pero internamente
    delega a la misma lógica de interpretación que CU30.

    Flow:
    1. Validar autenticación
    2. Validar capacidad SaaS (reportes_generativos_ia)
    3. Procesar solicitud via SolicitarReporteGenerativoService
    4. Retornar interpretación y datos
    """,
)
async def solicitar_reporte_generativo(
    payload: ConsultaInteligenteRequest,
    actor: Usuario = Depends(require_administrador),
    db: Session = Depends(get_db),
) -> ConsultaInteligenteResponse:
    """Procesa una solicitud de reporte generativo."""

    service = SolicitarReporteGenerativoService(db)

    try:
        return service.procesar_solicitud(payload, actor)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
