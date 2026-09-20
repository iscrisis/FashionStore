"""Contratos de entrada/salida de CU14 -- Consultar inventario (Panel del Encargado)."""

from pydantic import BaseModel, ConfigDict, Field


class CiudadResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class SucursalDelEncargadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    ciudad: CiudadResumen


class TallaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ColorResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class VarianteStockOut(BaseModel):
    id: int
    talla: TallaResumen
    color: ColorResumen
    # cantidad = stock físico real (el que edita este panel vía "Registrar
    # movimiento", CU16) -- reservar (CU17) NUNCA lo cambia. stock_reservado y
    # disponible se agregan para que el Encargado vea también lo comprometido
    # por reservas PENDIENTES, sin que esto habilite ninguna edición nueva
    # aquí (ver CU17_CrearReservaPrendas para quién escribe stock_reservado).
    cantidad: int
    stock_reservado: int
    disponible: int


class TemporadaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class CategoriaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ColeccionConTemporadaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    temporada: TemporadaResumen


class ProductoInventarioOut(BaseModel):
    id: int
    nombre: str
    imagen_principal_url: str | None
    categoria: CategoriaResumen
    coleccion: ColeccionConTemporadaResumen
    variantes: list[VarianteStockOut]


class StockItem(BaseModel):
    producto_variante_id: int
    cantidad: int = Field(ge=0)


class ActualizarStockLoteRequest(BaseModel):
    items: list[StockItem]
