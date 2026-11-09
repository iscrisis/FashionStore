"""Endpoints de CU11 — Sincronizar operaciones pendientes.

Acepta solicitudes desde Angular (IndexedDB) y Flutter (SQLite).
Ambos clientes usan el mismo contrato REST.

Endpoints:
- POST /sincronizar/ventas — Sincronizar venta presencial offline
- POST /sincronizar/reservas — Sincronizar reserva offline
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

logger = logging.getLogger(__name__)

from .schemas import (
    ResultadoSincronizacionVenta,
    ResultadoSincronizacionReserva,
    SincronizarVentaOfflineIn,
    SincronizarReservaOfflineIn,
)
from .service import (
    SincronizarOperacionesPendientesService,
    ValidacionError,
)

router = APIRouter(
    prefix="/sincronizar",
    tags=["CU11 - Sincronizar operaciones pendientes"],
)


@router.post(
    "/ventas",
    response_model=ResultadoSincronizacionVenta,
    status_code=status.HTTP_201_CREATED,
)
def sincronizar_venta(
    operacion: SincronizarVentaOfflineIn,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> ResultadoSincronizacionVenta:
    """Sincronizar venta presencial offline.

    Requiere: Usuario autenticado (puede ser CAJERO o CLIENTE/ADMINISTRADOR)

    Validaciones:
    - UUID único (idempotencia)
    - Empresa y sucursal del actor
    - Estructura completa de detalles
    - Stock disponible
    - Pago exclusivamente en EFECTIVO

    Respuesta:
    - CONFIRMADA: Venta registrada
    - RECHAZADA: Error de validación o negocio
    - CONFLICTO: Stock insuficiente u otro conflicto resoluble
    """
    try:
        service = SincronizarOperacionesPendientesService(db)
        resultado = service.sincronizar_venta_offline(actor, operacion)

        # NUEVO: Registrar conflicto automáticamente en CU14 (idempotente por UUID)
        if resultado.estado == "CONFLICTO":
            try:
                from modules.PK09_SincronizacionYConsistencia.CU14_GestionarConflictosSincronizacion.service import GestionarConflictosService
                cu14_service = GestionarConflictosService(db)
                cu14_service.registrar_conflicto_desde_resultado_cu11(actor, resultado)
                db.commit()
            except Exception as e:
                logger.exception("[CU11] Error registrando conflicto en CU14: %s", str(e))
                # No lanzar: si falla CU14, CU11 sigue devolviendo el conflicto normalmente

        # HTTP 201 si fue confirmada, 422 si hay conflicto o rechazo
        if resultado.estado == "CONFIRMADA":
            return resultado
        elif resultado.estado == "CONFLICTO":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=resultado.motivo or "Conflicto al procesar operación",
            )
        else:  # RECHAZADA
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=resultado.motivo or "No se pudo procesar la operación",
            )

    except ValidacionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.exception("[CU11] Error interno. Detalles: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        ) from e


@router.post(
    "/reservas",
    response_model=ResultadoSincronizacionReserva,
    status_code=status.HTTP_201_CREATED,
)
def sincronizar_reserva(
    operacion: SincronizarReservaOfflineIn,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> ResultadoSincronizacionReserva:
    """Sincronizar reserva presencial offline.

    Requiere: Usuario autenticado (cliente que hizo la reserva offline)

    Validaciones:
    - UUID único (idempotencia)
    - Empresa y sucursal del actor
    - Cliente debe ser el mismo que el actor
    - Estructura completa de detalles
    - Stock disponible en servidor

    Respuesta:
    - CONFIRMADA: Reserva registrada
    - RECHAZADA: Error de validación o negocio
    - CONFLICTO: Stock insuficiente
    """
    try:
        service = SincronizarOperacionesPendientesService(db)
        resultado = service.sincronizar_reserva_offline(actor, operacion)

        # NUEVO: Registrar conflicto automáticamente en CU14 (idempotente por UUID)
        if resultado.estado == "CONFLICTO":
            try:
                from modules.PK09_SincronizacionYConsistencia.CU14_GestionarConflictosSincronizacion.service import GestionarConflictosService
                cu14_service = GestionarConflictosService(db)
                cu14_service.registrar_conflicto_desde_resultado_cu11(actor, resultado)
                db.commit()
            except Exception as e:
                logger.exception("[CU11] Error registrando conflicto en CU14: %s", str(e))
                # No lanzar: si falla CU14, CU11 sigue devolviendo el conflicto normalmente

        # HTTP 201 si fue confirmada, 422 si hay conflicto o rechazo
        if resultado.estado == "CONFIRMADA":
            return resultado
        elif resultado.estado == "CONFLICTO":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=resultado.motivo or "Conflicto al procesar operación",
            )
        else:  # RECHAZADA
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=resultado.motivo or "No se pudo procesar la operación",
            )

    except ValidacionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.exception("[CU11] Error interno. Detalles: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        ) from e
