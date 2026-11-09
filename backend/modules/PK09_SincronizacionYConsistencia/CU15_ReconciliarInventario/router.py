"""Endpoints para CU15 — Reconciliar inventario."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .service import ReconciliarInventarioService
from .schemas import (
    ResultadoReconciliacion,
    ConsultaReconciliacionRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reconciliar",
    tags=["CU15 - Reconciliar inventario"],
)


@router.post(
    "/ventas/{uuid_operacion}",
    response_model=ResultadoReconciliacion,
    status_code=status.HTTP_200_OK,
)
def reconciliar_venta(
    uuid_operacion: str,
    empresa_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> ResultadoReconciliacion:
    """Reconciliar inventario de una venta offline confirmada.

    Verifica consistencia sin aplicar ajustes automáticos.

    Requiere: Usuario autenticado con rol CAJERO o ADMINISTRADOR

    Estados posibles:
    - CONSISTENTE: Inventario coincide con operación
    - DIVERGENCIA_DETECTADA: Se encontraron diferencias de stock
    - PENDIENTE_REVISION: Datos insuficientes para determinar consistencia
    """
    try:
        request = ConsultaReconciliacionRequest(
            uuid_operacion_offline=uuid_operacion,
            tipo_operacion="VENTA_OFFLINE",
            empresa_id=empresa_id,
        )

        service = ReconciliarInventarioService(db)
        resultado = service.reconciliar_venta_offline(actor, request)

        return resultado

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.exception("[CU15] Error reconciliando venta: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        ) from e


@router.post(
    "/reservas/{uuid_operacion}",
    response_model=ResultadoReconciliacion,
    status_code=status.HTTP_200_OK,
)
def reconciliar_reserva(
    uuid_operacion: str,
    empresa_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> ResultadoReconciliacion:
    """Reconciliar inventario de una reserva offline confirmada.

    Verifica consistencia sin aplicar ajustes automáticos.

    Requiere: Usuario autenticado

    Estados posibles:
    - CONSISTENTE: Inventario coincide con reserva
    - DIVERGENCIA_DETECTADA: Se encontraron diferencias de stock
    - PENDIENTE_REVISION: Datos insuficientes para determinar consistencia
    """
    try:
        request = ConsultaReconciliacionRequest(
            uuid_operacion_offline=uuid_operacion,
            tipo_operacion="RESERVA_OFFLINE",
            empresa_id=empresa_id,
        )

        service = ReconciliarInventarioService(db)
        resultado = service.reconciliar_reserva_offline(actor, request)

        return resultado

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.exception("[CU15] Error reconciliando reserva: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        ) from e
