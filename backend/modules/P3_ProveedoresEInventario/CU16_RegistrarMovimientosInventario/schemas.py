"""Contratos de entrada/salida de CU16 -- Registrar movimientos de inventario (Panel del Encargado)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TipoMovimiento = Literal["AJUSTE_POSITIVO", "AJUSTE_NEGATIVO"]


class TallaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ColorResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class VarianteResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    talla: TallaResumen
    color: ColorResumen


class VarianteConStockOut(BaseModel):
    id: int
    talla: TallaResumen
    color: ColorResumen
    cantidad: int


class ProductoConVariantesOut(BaseModel):
    id: int
    nombre: str
    imagen_principal_url: str | None
    variantes: list[VarianteConStockOut]


class ProductoResumen(BaseModel):
    id: int
    nombre: str
    imagen_principal_url: str | None


class UsuarioResumen(BaseModel):
    id: int
    nombre: str


class MovimientoOut(BaseModel):
    id: int
    producto: ProductoResumen
    variante: VarianteResumen
    tipo: TipoMovimiento
    cantidad: int
    motivo: str
    stock_anterior: int
    stock_resultante: int
    fecha_hora: datetime
    registrado_por: UsuarioResumen


class RegistrarMovimientoRequest(BaseModel):
    producto_variante_id: int
    tipo: TipoMovimiento
    cantidad: int = Field(gt=0)
    motivo: str

    @field_validator("motivo")
    @classmethod
    def _validar_motivo(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 3:
            raise ValueError("El motivo debe tener al menos 3 caracteres.")
        if len(limpio) > 300:
            raise ValueError("El motivo no puede superar los 300 caracteres.")
        return limpio
