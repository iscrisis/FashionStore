"""Schemas de CU05 — Gestionar suscripción de empresa."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class PlanResumenDTO(BaseModel):
    """Resumen del plan para consulta en suscripción."""
    id: int
    nombre: str
    slug: str
    descripcion: str
    precio: Decimal
    limite_sucursales: int
    limite_usuarios: int
    gestion_productos: bool
    gestion_ventas: bool
    reservas: bool
    operacion_offline: bool
    reportes_convencionales: bool
    reportes_generativos_ia: bool
    is_active: bool

    class Config:
        from_attributes = True


class EmpresaResumenDTO(BaseModel):
    """Resumen de empresa para gestión de suscripciones."""
    id: int
    nombre: str
    razon_social: str

    class Config:
        from_attributes = True


class SuscripcionBase(BaseModel):
    """Base para suscripción."""
    empresa_id: int = Field(..., gt=0)
    plan_id: int = Field(..., gt=0)
    fecha_inicio: datetime
    fecha_vencimiento: datetime
    activa: bool = True


class SuscripcionCrear(BaseModel):
    """DTO para crear suscripción."""
    empresa_id: int = Field(..., gt=0)
    plan_id: int = Field(..., gt=0)
    fecha_inicio: datetime
    fecha_vencimiento: datetime


class SuscripcionActualizar(BaseModel):
    """DTO para actualizar suscripción."""
    plan_id: int | None = Field(None, gt=0)
    fecha_vencimiento: datetime | None = None
    activa: bool | None = None


class SuscripcionRenovar(BaseModel):
    """DTO para renovar suscripción."""
    fecha_vencimiento: datetime = Field(..., description="Nueva fecha de vencimiento")


class SuscripcionCambiarEstado(BaseModel):
    """DTO para cambiar estado de suscripción."""
    activa: bool


class SuscripcionResponse(SuscripcionBase):
    """DTO de respuesta para suscripción."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SuscripcionConDetalleResponse(BaseModel):
    """Suscripción con detalle completo de empresa y plan."""
    suscripcion: SuscripcionResponse | None
    empresa: EmpresaResumenDTO
    plan: PlanResumenDTO | None
    funcionalidades_habilitadas: dict

    class Config:
        from_attributes = True


class ListaEmpresasSuscripciones(BaseModel):
    """Lista de empresas con suscripciones."""
    id: int
    nombre: str
    razon_social: str
    suscripcion: SuscripcionResponse | None
    plan: PlanResumenDTO | None

    class Config:
        from_attributes = True
