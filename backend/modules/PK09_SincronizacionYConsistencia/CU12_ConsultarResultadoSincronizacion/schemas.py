"""Esquemas de entrada/salida para CU12 — Consultar resultado de sincronización."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ResultadoSincronizacionOut(BaseModel):
    """Resultado consultable de una operación sincronizada."""

    uuid_local: str = Field(..., description="UUID único de la operación en IndexedDB")
    tipo_operacion: Literal["VENTA_OFFLINE", "RESERVA_OFFLINE"]
    estado: Literal["CONFIRMADA", "RECHAZADA", "CONFLICTO"]
    motivo: str | None = Field(None, description="Razón del rechazo o conflicto")

    # Identificadores oficiales (si fue confirmada)
    venta_id: int | None = Field(None, description="ID oficial de venta en PostgreSQL")
    reserva_id: int | None = Field(None, description="ID oficial de reserva en PostgreSQL")
    codigo_venta: str | None = Field(None, description="Código legible de venta")
    codigo_reserva: str | None = Field(None, description="Código legible de reserva")

    # Información temporal
    fecha_local: datetime = Field(..., description="Cuándo se registró localmente")
    fecha_sincronizacion: datetime | None = Field(None, description="Cuándo se sincronizó")

    # Información de negocio
    total: Decimal | None = Field(None, description="Total de la venta")
    empresa_id: int
    sucursal_id: int


class ResumenResultadosSincronizacion(BaseModel):
    """Resumen de conteos de resultados para un usuario."""

    confirmadas: int = Field(0, description="Operaciones confirmadas")
    pendientes: int = Field(0, description="Operaciones pendientes de sincronización")
    rechazadas: int = Field(0, description="Operaciones rechazadas")
    conflictos: int = Field(0, description="Operaciones con conflicto")
    total: int = Field(0, description="Total de operaciones")
