"""Reglas de negocio de CU12 -- Consultar disponibilidad por sucursal (público).

Solo lectura: no crea, modifica ni borra stock -- eso sigue siendo exclusivo
del Encargado (ver CU14_ConsultarInventario). Para un producto, cruza cada una de
sus variantes (talla + color, CU08) con cada sucursal (CU06) y con
StockSucursal (fuente real de existencias) para armar, por sucursal, la
cantidad real de cada variante -- es la base que necesitará el futuro flujo
de reservas para saber en qué sucursal y con qué variante puede reservar un
Cliente.
"""

from sqlalchemy.orm import Session

from .repository import DisponibilidadLecturaRepository
from .schemas import DisponibilidadSucursalOut, ProductoDisponibilidadOut, VarianteDisponibleOut


class ProductoNoEncontradoError(Exception):
    """El producto indicado no existe o no está activo."""


class DisponibilidadService:
    def __init__(self, db: Session):
        self._repo = DisponibilidadLecturaRepository(db)

    def consultar_por_producto(
        self, producto_id: int, ciudad_id: int | None
    ) -> ProductoDisponibilidadOut:
        producto = self._repo.get_producto_activo(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError

        variantes = sorted(
            (v for v in producto.variantes if v.is_active),
            key=lambda v: (v.color.nombre, v.talla.nombre),
        )
        sucursales = self._repo.listar_sucursales_activas(ciudad_id)
        cantidades = self._repo.cantidades_por_variantes([v.id for v in variantes])

        disponibilidad = [
            DisponibilidadSucursalOut(
                sucursal_id=sucursal.id,
                sucursal=sucursal.nombre,
                ciudad_id=sucursal.ciudad_id,
                ciudad=sucursal.ciudad.nombre,
                variantes=[
                    VarianteDisponibleOut(
                        producto_variante_id=variante.id,
                        talla_id=variante.talla_id,
                        talla=variante.talla.nombre,
                        color_id=variante.color_id,
                        color=variante.color.nombre,
                        cantidad=cantidades.get((sucursal.id, variante.id), 0),
                    )
                    for variante in variantes
                ],
            )
            for sucursal in sucursales
        ]
        return ProductoDisponibilidadOut(producto_id=producto.id, disponibilidad=disponibilidad)
