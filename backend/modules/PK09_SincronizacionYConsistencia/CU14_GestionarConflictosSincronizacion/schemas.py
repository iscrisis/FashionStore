"""Esquemas de entrada/salida para CU14 — Gestionar conflictos de sincronización."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


# ============================================================================
# DETECCIÓN Y REGISTRO DE CONFLICTOS
# ============================================================================

class ConflictoDetectadoSchema(BaseModel):
    """Conflicto detectado durante la sincronización."""

    uuid_operacion_offline: str = Field(..., description="UUID de la operación original")
    tipo_operacion: Literal["VENTA_OFFLINE", "RESERVA_OFFLINE"]
    tipo_conflicto: Literal[
        "STOCK_INSUFICIENTE",
        "VARIANTE_NO_DISPONIBLE",
        "INCONSISTENCIA_DATOS",
        "OTROS",
    ]
    motivo: str = Field(..., description="Descripción del conflicto")
    detalles_conflicto: str | None = Field(None, description="JSON con detalles técnicos")


class ConflictoRegistroSchema(BaseModel):
    """Respuesta al registrar un conflicto."""

    id: int
    uuid_operacion_offline: str
    tipo_conflicto: str
    estado_conflicto: Literal["DETECTADO", "RESUELTO", "DESCARTADO", "PENDIENTE_MANUAL"]
    fecha_detectado: datetime
    debe_reintentarse_automaticamente: bool = False


# ============================================================================
# CONSULTA DE CONFLICTOS
# ============================================================================

class ConflictoConsultaSchema(BaseModel):
    """Datos de un conflicto para consulta."""

    id: int
    uuid_operacion_offline: str
    tipo_operacion: Literal["VENTA_OFFLINE", "RESERVA_OFFLINE"]
    tipo_conflicto: str
    motivo: str | None
    detalles_conflicto: str | None
    estado_conflicto: str
    fecha_detectado: datetime
    usuario_id: int | None
    debe_reintentarse_automaticamente: bool


class ListaConflictosSchema(BaseModel):
    """Lista de conflictos sin resolver."""

    total: int
    conflictos: list[ConflictoConsultaSchema]


# ============================================================================
# RESOLUCIÓN DE CONFLICTOS
# ============================================================================

class ResolverConflictoRequest(BaseModel):
    """Solicitud de resolución de conflicto."""

    accion: Literal["DESCARTAR", "REINTENTAR_MANUAL", "MODIFICAR"]
    motivo_resolucion: str | None = Field(None, description="Justificación de la acción")


class ResolverConflictoResponse(BaseModel):
    """Respuesta al resolver un conflicto."""

    id: int
    uuid_operacion_offline: str
    estado_conflicto: str
    fecha_resolucion: datetime
    accion: str
