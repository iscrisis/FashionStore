"""Reglas de negocio de CU14 -- Consultar inventario (Panel del Encargado).

sucursal_id llega SIEMPRE ya resuelto desde el usuario autenticado (ver
_sucursal_id_del_actor en router.py), nunca desde un id que el cliente pueda
manipular -- así se garantiza que un ENCARGADO_SUCURSAL solo vea/edite el
stock de SU sucursal.
"""

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal

from .repository import ProductoLecturaRepository, StockSucursalRepository, SucursalLecturaRepository
from .schemas import (
    CategoriaResumen,
    ColeccionConTemporadaResumen,
    ColorResumen,
    ProductoInventarioOut,
    StockItem,
    TallaResumen,
    TemporadaResumen,
    VarianteStockOut,
)


class SucursalNoEncontradaError(Exception):
    pass


class VarianteNoEncontradaError(Exception):
    """La variante indicada no existe o está inactiva."""


class StockSucursalService:
    def __init__(self, db: Session):
        self._sucursales = SucursalLecturaRepository(db)
        self._productos = ProductoLecturaRepository(db)
        self._stock = StockSucursalRepository(db)

    def mi_sucursal(self, sucursal_id: int) -> Sucursal:
        sucursal = self._sucursales.get_by_id(sucursal_id)
        if sucursal is None:
            raise SucursalNoEncontradaError
        return sucursal

    def listar_inventario(
        self, sucursal_id: int, search: str | None
    ) -> list[ProductoInventarioOut]:
        productos = self._productos.listar_activos(search)
        stock_por_variante = self._stock.listar_por_sucursal(sucursal_id)

        resultado: list[ProductoInventarioOut] = []
        for producto in productos:
            variantes_activas = [v for v in producto.variantes if v.is_active]
            if not variantes_activas:
                continue
            resultado.append(
                ProductoInventarioOut(
                    id=producto.id,
                    nombre=producto.nombre,
                    imagen_principal_url=producto.imagen_principal_url,
                    categoria=CategoriaResumen.model_validate(producto.categoria),
                    coleccion=ColeccionConTemporadaResumen(
                        id=producto.coleccion.id,
                        nombre=producto.coleccion.nombre,
                        temporada=TemporadaResumen.model_validate(producto.coleccion.temporada),
                    ),
                    variantes=[
                        self._variante_stock_out(variante, stock_por_variante.get(variante.id))
                        for variante in variantes_activas
                    ],
                )
            )
        return resultado

    @staticmethod
    def _variante_stock_out(
        variante: ProductoVariante, fila_stock: StockSucursal | None
    ) -> VarianteStockOut:
        # Sin fila de stock todavía (nunca se cargó cantidad para esta
        # sucursal+variante): físico, reservado y disponible son 0, igual
        # que ya asumía este panel antes de agregar stock_reservado.
        cantidad = fila_stock.cantidad if fila_stock is not None else 0
        stock_reservado = fila_stock.stock_reservado if fila_stock is not None else 0
        return VarianteStockOut(
            id=variante.id,
            talla=TallaResumen.model_validate(variante.talla),
            color=ColorResumen.model_validate(variante.color),
            cantidad=cantidad,
            stock_reservado=stock_reservado,
            disponible=max(0, cantidad - stock_reservado),
        )

    def actualizar_stock(self, sucursal_id: int, items: list[StockItem]) -> list[StockItem]:
        for item in items:
            variante = self._productos.get_variante_by_id(item.producto_variante_id)
            if variante is None or not variante.is_active:
                raise VarianteNoEncontradaError

        for item in items:
            self._stock.upsert(sucursal_id, item.producto_variante_id, item.cantidad)
        self._stock.guardar_todo()
        return items
