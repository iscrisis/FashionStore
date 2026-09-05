"""Contratos de entrada/salida de CU08 -- Gestionar productos."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class ProveedorResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    razon_social: str


class CategoriaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class TemporadaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ColeccionResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class TallaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ColorResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ProductoImagenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    orden: int


class ProductoVarianteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    talla: TallaResumen
    color: ColorResumen
    is_active: bool


class ProductoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None
    precio_venta: Decimal
    is_active: bool
    proveedor: ProveedorResumen
    producto_proveedor_id: int | None
    categoria: CategoriaResumen
    temporada: TemporadaResumen
    coleccion: ColeccionResumen
    tallas: list[TallaResumen]
    colores: list[ColorResumen]
    variantes: list[ProductoVarianteOut]
    imagen_principal_url: str | None
    imagenes: list[ProductoImagenOut]


class _ProductoDatosBase(BaseModel):
    nombre: str
    descripcion: str | None = None
    proveedor_id: int
    producto_proveedor_id: int | None = None
    categoria_id: int
    temporada_id: int
    coleccion_id: int
    precio_venta: Decimal
    talla_ids: list[int]
    color_ids: list[int]

    @field_validator("nombre")
    @classmethod
    def _validar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre del producto debe tener al menos 2 caracteres.")
        if len(limpio) > 150:
            raise ValueError("El nombre no puede superar los 150 caracteres.")
        return limpio

    @field_validator("descripcion")
    @classmethod
    def _validar_descripcion(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        if len(limpio) > 500:
            raise ValueError("La descripción no puede superar los 500 caracteres.")
        return limpio or None

    @field_validator("precio_venta")
    @classmethod
    def _validar_precio(cls, valor: Decimal) -> Decimal:
        if valor <= 0:
            raise ValueError("El precio de venta debe ser mayor a 0.")
        return valor

    @field_validator("talla_ids")
    @classmethod
    def _validar_tallas(cls, valor: list[int]) -> list[int]:
        if not valor:
            raise ValueError("Selecciona al menos una talla.")
        if len(set(valor)) != len(valor):
            raise ValueError("No repitas la misma talla.")
        return valor

    @field_validator("color_ids")
    @classmethod
    def _validar_colores(cls, valor: list[int]) -> list[int]:
        if not valor:
            raise ValueError("Selecciona al menos un color.")
        if len(set(valor)) != len(valor):
            raise ValueError("No repitas el mismo color.")
        return valor


class ProductoCrear(_ProductoDatosBase):
    is_active: bool = True


class ProductoActualizar(_ProductoDatosBase):
    pass


class CambiarEstadoRequest(BaseModel):
    is_active: bool


class PropuestaProveedorOut(BaseModel):
    """Propuesta enviada por un proveedor (ProductoProveedor) todavía no
    convertida en un producto de FashionStore -- para que el Administrador la
    seleccione y complete los datos comerciales que le faltan."""

    id: int
    nombre: str
    descripcion: str | None
    disponibilidad: bool
    proveedor: ProveedorResumen
    temporada: TemporadaResumen
    coleccion: ColeccionResumen
