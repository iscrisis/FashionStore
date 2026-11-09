"""Router para CU14 — Gestionar conflictos de sincronización."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario
from app.db.session import get_db
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .service import GestionarConflictosService
from .schemas import (
    ListaConflictosSchema,
    ConflictoConsultaSchema,
    ResolverConflictoRequest,
    ResolverConflictoResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conflictos", tags=["CU14 - Gestionar conflictos de sincronización"])


# ============================================================================
# ENDPOINT: Consultar conflictos sin resolver
# ============================================================================

@router.get(
    "/sin-resolver",
    response_model=ListaConflictosSchema,
    summary="Consultar conflictos sin resolver",
)
def consultar_conflictos_sin_resolver(
    limit: int = 100,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> ListaConflictosSchema:
    """Obtener la lista de conflictos sin resolver para la empresa del usuario.

    Este endpoint retorna conflictos detectados durante la sincronización (CU11)
    que requieren intervención manual o decisión del usuario.

    Los conflictos son:
    - STOCK_INSUFICIENTE: No hay stock suficiente en el servidor
    - VARIANTE_NO_DISPONIBLE: La variante ya no está disponible
    - INCONSISTENCIA_DATOS: Inconsistencias entre datos locales y servidor
    - OTROS: Otros conflictos no categorizados

    El usuario debe resolver cada conflicto descartándolo o marcándolo para reintentar.
    """

    service = GestionarConflictosService(db)
    return service.obtener_conflictos_sin_resolver(actor, limit)


# ============================================================================
# ENDPOINT: Consultar conflicto específico
# ============================================================================

@router.get(
    "/{uuid_operacion}",
    response_model=ConflictoConsultaSchema | None,
    summary="Consultar conflicto por UUID",
)
def consultar_conflicto(
    uuid_operacion: str,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> ConflictoConsultaSchema | None:
    """Obtener detalles de un conflicto específico por UUID de la operación original.

    Retorna None si el conflicto no existe o ya ha sido resuelto.
    """

    service = GestionarConflictosService(db)
    conflicto = service.obtener_conflicto_por_uuid(actor, uuid_operacion)

    if not conflicto:
        raise HTTPException(status_code=404, detail="Conflicto no encontrado")

    return conflicto


# ============================================================================
# ENDPOINT: Resolver conflicto
# ============================================================================

@router.post(
    "/{conflicto_id}/resolver",
    response_model=ResolverConflictoResponse,
    summary="Resolver un conflicto",
)
def resolver_conflicto(
    conflicto_id: int,
    request: ResolverConflictoRequest,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_usuario),
) -> ResolverConflictoResponse:
    """Resolver un conflicto.

    Acciones disponibles:
    - DESCARTAR: Rechazar la operación sin reintentar
    - REINTENTAR_MANUAL: Marcar para reintentar manualmente más tarde
    - MODIFICAR: (Futuro) Modificar la operación y reintentar

    Solo usuarios autorizados (CAJERO, ADMINISTRADOR) pueden resolver conflictos.
    """

    if actor.rol not in ["CAJERO", "ADMINISTRADOR"]:
        raise HTTPException(status_code=403, detail="No autorizado para resolver conflictos")

    service = GestionarConflictosService(db)

    try:
        return service.resolver_conflicto(actor, conflicto_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("[CU14] Error resolviendo conflicto: %s", str(e))
        raise HTTPException(status_code=500, detail="Error al resolver conflicto")
