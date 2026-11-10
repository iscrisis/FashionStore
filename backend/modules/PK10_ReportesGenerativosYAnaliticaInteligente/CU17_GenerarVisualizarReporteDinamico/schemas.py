"""Esquemas de CU17 -- Solicitud y respuesta de reporte dinámico."""

from datetime import date
from pydantic import BaseModel, Field
from typing import Optional


class GenerarReporteDinamicoRequest(BaseModel):
    """Solicitud de generación de reporte dinámico con filtros."""

    fecha_desde: Optional[date] = Field(
        None, description="Fecha inicio (inclusiva). None = desde el principio"
    )
    fecha_hasta: Optional[date] = Field(
        None, description="Fecha fin (inclusiva). None = hasta hoy"
    )
    sucursal_id: Optional[int] = Field(
        None, description="ID de sucursal. None = todas las sucursales"
    )
    categoria_id: Optional[int] = Field(
        None, description="ID de categoría de producto. None = todas las categorías"
    )
    producto_id: Optional[int] = Field(
        None, description="ID de producto. None = todos los productos"
    )
    tipo_reporte: str = Field(
        default="completo",
        description="Tipo de reporte: 'completo', 'ventas', 'inventario', 'productos'",
    )


class GenerarReporteDinamicoResponse(BaseModel):
    """Respuesta con datos del reporte dinámico."""

    tipo_reporte: str
    exito: bool = True
    mensaje: Optional[str] = None
    filtros_aplicados: dict
    resumen: Optional[dict] = None
    datos: dict


class ReporteDinamicoMetadatos(BaseModel):
    """Metadatos del reporte generado."""

    fecha_generacion: str
    rango_datos: dict
    filtros: dict
    empresa_id: int
    usuario_id: int
