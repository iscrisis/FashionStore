"""Acceso a datos de CU21 -- Usar carrito de compras (Cliente).

Reutiliza ProductoVariante/Producto (CU08) y StockSucursal (CU14/15/16, en
SOLO LECTURA -- CU21 nunca escribe ninguna de sus columnas, ver service.py)
tal cual existen. Las tablas propias de este módulo son Carrito y
CarritoItem.

`bloquear_por_cliente` usa SELECT ... FOR UPDATE sobre la fila Carrito misma
(no sobre sus items) a propósito: agregar_item/actualizar_seleccion/
eliminar_item siempre bloquean primero el CARRITO completo antes de leer o
mutar su colección de items -- así dos requests concurrentes del MISMO
Cliente (doble clic, dos pestañas) leen siempre la colección ya actualizada
de la otra antes de decidir (ver CarritoService.agregar_item).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P5_ComprasVentasYPagos.Models.carrito import Carrito, CarritoItem


class CarritoRepository:
    def __init__(self, db: Session):
        self.db = db

    def bloquear_por_cliente(self, cliente_id: int) -> Carrito | None:
        """SELECT ... FOR UPDATE sobre la fila Carrito -- None si ese
        Cliente todavía no tiene carrito creado (ver
        CarritoService._obtener_o_crear_bloqueado, que lo crea la primera
        vez)."""
        stmt = (
            select(Carrito)
            .where(Carrito.cliente_id == cliente_id)
            .options(selectinload(Carrito.items).selectinload(CarritoItem.producto_variante))
            .with_for_update(of=Carrito)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def crear(self, cliente_id: int) -> Carrito:
        carrito = Carrito(cliente_id=cliente_id)
        self.db.add(carrito)
        self.db.commit()
        return carrito

    def guardar(self) -> None:
        self.db.commit()

    def refrescar(self, carrito: Carrito) -> None:
        self.db.refresh(carrito)


class ProductoVarianteLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_variante_activa_by_id(self, variante_id: int) -> ProductoVariante | None:
        variante = self.db.get(ProductoVariante, variante_id)
        if variante is None or not variante.is_active:
            return None
        return variante


class ProductoLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_producto_activo(self, producto_id: int) -> Producto | None:
        producto = self.db.get(Producto, producto_id)
        if producto is None or not producto.is_active:
            return None
        return producto

    def get_activos_by_ids(self, producto_ids: set[int]) -> dict[int, Producto]:
        """Una sola consulta para TODOS los productos del carrito (evita N
        consultas, una por item, al armar la salida -- ver
        CarritoService._a_salida). Solo activos: un producto desactivado
        después de agregarse simplemente no aparece en el dict, y ese item
        se omite en la salida, igual que get_producto_activo."""
        if not producto_ids:
            return {}
        stmt = select(Producto).where(Producto.id.in_(producto_ids), Producto.is_active.is_(True))
        return {p.id: p for p in self.db.execute(stmt).scalars()}


class StockSucursalRepository:
    def __init__(self, db: Session):
        self.db = db

    def alguna_sucursal_activa_cubre(self, variante_id: int, cantidad: int) -> bool:
        """True si AL MENOS UNA sucursal activa tiene, para esa variante,
        `cantidad_fisica - stock_reservado >= cantidad` -- CU21 no elige
        sucursal todavía (eso es de un CU posterior), así que solo confirma
        que la cantidad pedida sea técnicamente atendible por alguna, sin
        bloquear ni reservar nada (SELECT puro, sin FOR UPDATE: agregar al
        carrito nunca escribe stock, ver service.py)."""
        stmt = (
            select(StockSucursal.id)
            .join(Sucursal, StockSucursal.sucursal_id == Sucursal.id)
            .where(
                Sucursal.is_active.is_(True),
                StockSucursal.producto_variante_id == variante_id,
                (StockSucursal.cantidad - StockSucursal.stock_reservado) >= cantidad,
            )
            .limit(1)
        )
        return self.db.execute(stmt).first() is not None
