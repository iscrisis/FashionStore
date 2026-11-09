"""Esquemas de CU16 -- heredados de CU30.

CU16 reutiliza exactamente los mismos modelos de request/response que CU30,
ya que la responsabilidad de CU16 es solo gestionar el flujo de solicitud.
Los contratos permanecen idénticos.
"""

from modules.P6_InnovacionYAnalisis.CU30_ConsultarReportesIndicadores.schemas import (
    ConsultaInteligenteRequest,
    ConsultaInteligenteResponse,
)

__all__ = [
    "ConsultaInteligenteRequest",
    "ConsultaInteligenteResponse",
]
