"""Acceso de solo lectura de CU29 -- Obtener recomendaciones mediante IA.

Reutiliza al máximo lo que ya existe:
  - búsqueda de productos activos (filtrados por categoría/colección/talla/
    color): CatalogoPublicoRepository, la misma que ya usa CU11 -- nunca se
    duplica esa query aquí.
  - precio efectivo (base/final/promoción): precio_efectivo.py de CU32,
    llamado desde service.py, no desde este archivo.

Lo único NUEVO que aporta este repositorio es lo que ningún CU existente
necesitaba todavía:
  - resolver los NOMBRES sueltos que devuelve Gemini (o el resolver local
    sin IA) a los ids que CatalogoPublicoRepository.listar_productos ya
    espera (CatalogoResolverRepository);
  - un resumen de disponibilidad por producto, en texto simple, a partir de
    StockSucursal -- misma fuente y misma fórmula que CU12
    (cantidad - stock_reservado, nunca el físico crudo) pero agregada por
    producto en vez de por variante (DisponibilidadResumenRepository);
  - las compras PAGADAS reales de un Cliente para armar sus preferencias
    (PreferenciasClienteRepository) -- mismo Venta/VentaDetalle que ya lee
    CU27, en solo lectura, sin tocar su repositorio (la consulta es distinta:
    CU27 lista ventas, esto agrega variantes/categorías compradas).

Ninguna tabla propia. Ninguna escritura. Gemini nunca toca este archivo ni
ejecuta SQL -- es FastAPI quien lo llama, siempre desde service.py.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.CU11_ConsultarCatalogoPrendas.repository import (
    CatalogoPublicoRepository,
)
from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P5_ComprasVentasYPagos.Models.venta import EstadoVenta, Venta, VentaDetalle


class CatalogoResolverRepository:
    """Traduce nombres libres (los que extrae Gemini, o los que el resolver
    local sin IA encuentra dentro del mensaje) a los ids que
    CatalogoPublicoRepository.listar_productos ya recibe -- sin esto, CU29
    tendría que reescribir esa query con filtros por nombre en vez de id."""

    def __init__(self, db: Session):
        self._catalogo = CatalogoPublicoRepository(db)
        self._db = db

    def categorias_activas(self) -> list[Categoria]:
        return self._catalogo.listar_categorias_activas()

    def colores_activos(self) -> list[Color]:
        return self._catalogo.listar_colores_activos()

    def tallas_activas(self) -> list[Talla]:
        return self._catalogo.listar_tallas_activas()

    def colecciones_activas(self) -> list[Coleccion]:
        return self._catalogo.listar_colecciones_activas()

    def ciudades_activas(self) -> list[Ciudad]:
        stmt = select(Ciudad).where(Ciudad.is_active.is_(True)).order_by(Ciudad.nombre)
        return list(self._db.execute(stmt).scalars().all())

    @staticmethod
    def _mejor_coincidencia(nombre: str | None, opciones: list) -> int | None:
        """Coincidencia exacta primero (insensible a mayúsculas); si no,
        contención en cualquier sentido (ej. Gemini dice "chaquetas" y el
        catálogo tiene "Chaqueta", o al revés) -- nunca inventa un id que no
        exista en `opciones`."""
        if not nombre:
            return None
        objetivo = nombre.strip().lower()
        if not objetivo:
            return None
        for opcion in opciones:
            if opcion.nombre.strip().lower() == objetivo:
                return opcion.id
        for opcion in opciones:
            comparado = opcion.nombre.strip().lower()
            if objetivo in comparado or comparado in objetivo:
                return opcion.id
        return None

    def resolver_categoria_id(self, nombre: str | None) -> int | None:
        return self._mejor_coincidencia(nombre, self.categorias_activas())

    def resolver_color_id(self, nombre: str | None) -> int | None:
        return self._mejor_coincidencia(nombre, self.colores_activos())

    def resolver_talla_id(self, nombre: str | None) -> int | None:
        return self._mejor_coincidencia(nombre, self.tallas_activas())

    def resolver_coleccion_id(self, nombre: str | None) -> int | None:
        return self._mejor_coincidencia(nombre, self.colecciones_activas())

    def resolver_ciudad_id(self, nombre: str | None) -> int | None:
        return self._mejor_coincidencia(nombre, self.ciudades_activas())


class DisponibilidadResumenRepository:
    """Resumen textual de disponibilidad por producto -- misma fuente real
    que CU12 (StockSucursal, "disponible" SIEMPRE cantidad - stock_reservado,
    nunca el físico crudo), agregada por producto en vez de por variante
    porque el chat no necesita el detalle talla/color por sucursal, solo
    "en qué sucursales hay stock"."""

    def __init__(self, db: Session):
        self.db = db

    def sucursales_con_stock(
        self, producto_id: int, ciudad_id: int | None = None, limite_nombres: int = 2
    ) -> tuple[list[str], int]:
        stmt = (
            select(Sucursal.nombre, func.sum(StockSucursal.cantidad - StockSucursal.stock_reservado))
            .select_from(StockSucursal)
            .join(ProductoVariante, ProductoVariante.id == StockSucursal.producto_variante_id)
            .join(Sucursal, Sucursal.id == StockSucursal.sucursal_id)
            .where(
                ProductoVariante.producto_id == producto_id,
                ProductoVariante.is_active.is_(True),
                Sucursal.is_active.is_(True),
            )
        )
        if ciudad_id is not None:
            stmt = stmt.where(Sucursal.ciudad_id == ciudad_id)
        stmt = stmt.group_by(Sucursal.id, Sucursal.nombre).having(
            func.sum(StockSucursal.cantidad - StockSucursal.stock_reservado) > 0
        ).order_by(Sucursal.nombre)

        filas = self.db.execute(stmt).all()
        nombres = [nombre for nombre, _ in filas]
        return nombres[:limite_nombres], len(nombres)


class PreferenciasClienteRepository:
    """Compras PAGADAS reales de un Cliente -- misma Venta/VentaDetalle que
    ya lee CU27 (CU27_ConsultarHistorialCompras/repository.py), en solo
    lectura, sin reescribir su repositorio: aquí la forma de la consulta es
    distinta (se necesita cada VentaDetalle con su variante, no la Venta
    agregada)."""

    def __init__(self, db: Session):
        self.db = db

    def compras_recientes(self, cliente_id: int, limite: int = 20) -> list[VentaDetalle]:
        stmt = (
            select(VentaDetalle)
            .join(Venta, Venta.id == VentaDetalle.venta_id)
            .where(Venta.cliente_id == cliente_id, Venta.estado == EstadoVenta.PAGADA)
            .order_by(Venta.fecha_creacion.desc())
            .limit(limite)
        )
        return list(self.db.execute(stmt).scalars().all())

    def productos_por_ids(self, producto_ids: set[int]) -> dict[int, Producto]:
        if not producto_ids:
            return {}
        stmt = select(Producto).where(Producto.id.in_(producto_ids))
        return {producto.id: producto for producto in self.db.execute(stmt).scalars().all()}
