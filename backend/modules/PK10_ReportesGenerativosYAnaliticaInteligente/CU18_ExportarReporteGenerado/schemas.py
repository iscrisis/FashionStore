"""Esquemas de CU18 -- Solicitud y respuesta de exportación de reportes."""

from datetime import date
from pydantic import BaseModel, Field
from typing import Optional, Literal


class ExportarReporteRequest(BaseModel):
    """Solicitud de exportación de reporte dinámico a PDF o Excel."""

    formato: Literal["pdf", "xlsx"] = Field(
        description="Formato de exportación: 'pdf' o 'xlsx'"
    )
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


class ExportarReporteResponse(BaseModel):
    """Respuesta de exportación (metadatos del archivo)."""

    exito: bool = True
    mensaje: str
    nombre_archivo: str
    formato: str
    tamaño_bytes: int
