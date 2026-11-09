"""Endpoints de CU12 — Consultar resultado de sincronización.

API REST de solo lectura para consultar resultados persistidos en PostgreSQL.
Compatible con Flutter, sin ejecutar nuevas sincronizaciones.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .schemas import ResultadoSincronizacionOut, ResumenResultadosSincronizacion
from .service import ConsultarResultadoService

router = APIRouter(
    prefix="/resultados-sincronizacion",
    tags=["CU12 - Consultar resultado de sincronización"],
)


@router.get(
    "/venta/{uuid_local}",
    response_model=ResultadoSincronizacionOut,
    status_code=status.HTTP_200_OK,
)
def consultar_resultado_venta(
    uuid_local: str,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> ResultadoSincronizacionOut:
    """Consultar resultado de una venta offline sincronizada.

    Retorna la información si la venta existe en PostgreSQL con uuid_operacion_offline.

    Requiere: Usuario autenticado con rol ADMINISTRADOR o CAJERO.

    Respuesta:
    - 200 OK: Venta encontrada con su resultado.
    - 404 NOT FOUND: Venta no existe o usuario no autorizado.
    - 403 FORBIDDEN: Usuario no tiene permiso (rol o sucursal).
    """
    try:
        service = ConsultarResultadoService(db)
        resultado = service.consultar_resultado_venta(actor, uuid_local)

        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venta no encontrada o acceso denegado",
            )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        ) from e


@router.get(
    "/reserva/{uuid_local}",
    response_model=ResultadoSincronizacionOut,
    status_code=status.HTTP_200_OK,
)
def consultar_resultado_reserva(
    uuid_local: str,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> ResultadoSincronizacionOut:
    """Consultar resultado de una reserva offline sincronizada.

    Retorna la información si la reserva existe en PostgreSQL con uuid_operacion_offline.

    Requiere: Usuario autenticado (CLIENTE solo ve sus reservas, ADMINISTRADOR/CAJERO ven todas).

    Respuesta:
    - 200 OK: Reserva encontrada con su resultado.
    - 404 NOT FOUND: Reserva no existe o usuario no autorizado.
    - 403 FORBIDDEN: Cliente intenta acceder a reserva ajena.
    """
    try:
        service = ConsultarResultadoService(db)
        resultado = service.consultar_resultado_reserva(actor, uuid_local)

        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada o acceso denegado",
            )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        ) from e


@router.get(
    "/ventas",
    response_model=list[ResultadoSincronizacionOut],
    status_code=status.HTTP_200_OK,
)
def listar_resultados_ventas(
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> list[ResultadoSincronizacionOut]:
    """Listar todas las ventas sincronizadas autorizadas.

    Requiere: Usuario autenticado con rol ADMINISTRADOR o CAJERO.

    Respuesta: Array de ventas sincronizadas.
    """
    try:
        service = ConsultarResultadoService(db)
        return service.listar_resultados_venta(actor)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        ) from e


@router.get(
    "/reservas",
    response_model=list[ResultadoSincronizacionOut],
    status_code=status.HTTP_200_OK,
)
def listar_resultados_reservas(
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> list[ResultadoSincronizacionOut]:
    """Listar todas las reservas sincronizadas autorizadas.

    Requiere: Usuario autenticado.
    - CLIENTE: Ve solo sus reservas.
    - ADMINISTRADOR/CAJERO: Ven todas.

    Respuesta: Array de reservas sincronizadas.
    """
    try:
        service = ConsultarResultadoService(db)
        return service.listar_resultados_reserva(actor)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        ) from e


@router.get(
    "/resumen",
    response_model=ResumenResultadosSincronizacion,
    status_code=status.HTTP_200_OK,
)
def obtener_resumen(
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> ResumenResultadosSincronizacion:
    """Obtener resumen de conteos de resultados de sincronización.

    Retorna números de operaciones confirmadas, rechazadas, en conflicto, etc.

    Requiere: Usuario autenticado.
    """
    try:
        service = ConsultarResultadoService(db)
        return service.obtener_resumen(actor)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        ) from e
