"""Contratos de entrada/salida de CU15 -- Registrar recepción de mercadería (Panel del Encargado)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProveedorResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    razon_social: str


class TallaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ColorResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class VarianteParaRecepcionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    talla: TallaResumen
    color: ColorResumen


class CategoriaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ColeccionResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ProductoParaRecepcionOut(BaseModel):
    id: int
    nombre: str
    imagen_principal_url: str | None
    categoria: CategoriaResumen
    coleccion: ColeccionResumen
    variantes: list[VarianteParaRecepcionOut]


class SucursalResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class UsuarioResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ProductoResumen(BaseModel):
    id: int
    nombre: str
    imagen_principal_url: str | None


class DetalleRecepcionOut(BaseModel):
    producto: ProductoResumen
    variante: VarianteParaRecepcionOut
    cantidad_recibida: int
    stock_resultante: int


class RecepcionOut(BaseModel):
    id: int
    proveedor: ProveedorResumen
    sucursal: SucursalResumen
    registrado_por: UsuarioResumen
    fecha_hora: datetime
    observacion: str | None
    detalles: list[DetalleRecepcionOut]


class DetalleRecepcionRequest(BaseModel):
    producto_id: int
    producto_variante_id: int
    cantidad_recibida: int = Field(gt=0)


class RegistrarRecepcionRequest(BaseModel):
    proveedor_id: int
    observacion: str | None = Field(default=None, max_length=500)
    detalles: list[DetalleRecepcionRequest] = Field(min_length=1)
