"""Esquemas para CU13 — Reintentar sincronización fallida."""

from datetime import datetime
from typing import Literal
from decimal import Decimal
from pydantic import BaseModel, Field


class ReintentoRequest(BaseModel):
    """Solicitud para reintentar una operación fallida."""
    empresa_id: int = Field(..., description="ID de empresa (validación)")
    motivo_manual: str | None = Field(None, description="Razón por la que el usuario reintenta manualmente")


class ReintentoResultado(BaseModel):
    """Resultado de un intento de sincronización (CU11 reutilizado)."""
    uuid_local: str
    tipo_operacion: Literal["VENTA_OFFLINE", "RESERVA_OFFLINE"]
    estado: Literal["CONFIRMADA", "RECHAZADA", "CONFLICTO"]
    motivo: str | None
    # Venta
    venta_id: int | None = None
    codigo_venta: str | None = None
    total: Decimal | None = None
    # Reserva
    reserva_id: int | None = None
    codigo_reserva: str | None = None
    # Auditoría
    numero_intento: int
    proximo_reintento_en_ms: int = 0  # 0 = disponible ahora, >0 = esperar


class OperacionFallidaSummary(BaseModel):
    """Resumen de operación fallida para listados."""
    uuid: str
    tipo_operacion: Literal["VENTA_OFFLINE", "RESERVA_OFFLINE"]
    estado: Literal["RECHAZADA", "CONFLICTO"]
    motivo: str | None
    numero_intentos: int
    ultima_fecha_intento: datetime
    proximo_reintento_disponible_en_ms: int


class ResumenOperacionesFallidas(BaseModel):
    """Resumen de conteos de operaciones fallidas."""
    total_rechazadas: int = Field(0, description="Operaciones rechazadas (potencialmente recuperables)")
    total_conflictos: int = Field(0, description="Operaciones con conflicto de stock")
    total_con_reintentos_disponibles: int = Field(0, description="Operaciones elegibles para reintentar ahora")
    proximo_reintento_disponible_en_ms: int = Field(0, description="Tiempo hasta próximo reintento automático posible")


class BackoffConfig(BaseModel):
    """Configuración de política de reintentos (interna)."""
    max_intentos: int = 5
    backoff_ms: list[int] = [1000, 2000, 5000, 10000, 30000]  # ms: 1s, 2s, 5s, 10s, 30s

    def obtener_espera_ms(self, numero_intento: int) -> int:
        """Retorna milisegundos a esperar antes del intento N."""
        if numero_intento <= 0:
            return 0
        idx = min(numero_intento - 1, len(self.backoff_ms) - 1)
        return self.backoff_ms[idx]
