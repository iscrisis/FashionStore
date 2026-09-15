"""Acceso a datos de CU16 -- Registrar movimientos de inventario (Panel del Encargado).

Reutiliza Producto/ProductoVariante (CU08) y StockSucursal tal cual existen,
en solo lectura salvo el ajuste de cantidad. La única tabla nueva de este
módulo es MovimientoInventario.

El ajuste de StockSucursal vive en SU PROPIO repositorio (más abajo) en lugar
de reutilizar el de CU14 (que hace 'set' absoluto sin trazabilidad) o el de
CU15 (que siempre suma la recepción de un proveedor): CU16 fija un resultado
ya calculado por el servicio (stock_actual +/- cantidad, nunca negativo), una
operación distinta que no debe alterar el contrato de ninguno de los dos.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.movimiento_inventario import MovimientoInventario
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario


class ProductoLecturaRepository:
    """Solo lectura de Producto/ProductoVariante (CU08) para el panel del Encargado."""

    def __init__(self, db: Session):
        self.db = db

    def listar_activos(self, search: str | None = None) -> list[Producto]:
        stmt = select(Producto).where(Producto.is_active.is_(True))
        if search:
            patron = f"%{search.strip().lower()}%"
            stmt = stmt.where(func.lower(Producto.nombre).like(patron))
        stmt = stmt.order_by(Producto.nombre)
        return list(self.db.execute(stmt).scalars().unique().all())

    def get_by_id(self, producto_id: int) -> Producto | None:
        return self.db.get(Producto, producto_id)

    def get_variante_by_id(self, variante_id: int) -> ProductoVariante | None:
        return self.db.get(ProductoVariante, variante_id)


class StockAjusteRepository:
    """Escritura de StockSucursal propia de CU16: fija un resultado ya
    calculado (stock_actual +/- cantidad) -- no suma como CU15 ni reemplaza
    un valor arbitrario como CU14."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_sucursal_y_variante(
        self, sucursal_id: int, variante_id: int
    ) -> StockSucursal | None:
        stmt = select(StockSucursal).where(
            StockSucursal.sucursal_id == sucursal_id,
            StockSucursal.producto_variante_id == variante_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def listar_por_sucursal(self, sucursal_id: int) -> dict[int, int]:
        stmt = select(StockSucursal).where(StockSucursal.sucursal_id == sucursal_id)
        filas = self.db.execute(stmt).scalars().all()
        return {fila.producto_variante_id: fila.cantidad for fila in filas}

    def fijar_resultado(self, sucursal_id: int, variante_id: int, nuevo_valor: int) -> StockSucursal:
        stock = self.get_by_sucursal_y_variante(sucursal_id, variante_id)
        if stock is None:
            stock = StockSucursal(
                sucursal_id=sucursal_id, producto_variante_id=variante_id, cantidad=nuevo_valor
            )
            self.db.add(stock)
        else:
            stock.cantidad = nuevo_valor
        return stock


class MovimientoInventarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, movimiento: MovimientoInventario) -> MovimientoInventario:
        self.db.add(movimiento)
        self.db.flush()
        return movimiento

    def confirmar(self) -> None:
        self.db.commit()

    def listar_por_sucursal(self, sucursal_id: int, limit: int) -> list[MovimientoInventario]:
        stmt = (
            select(MovimientoInventario)
            .where(MovimientoInventario.sucursal_id == sucursal_id)
            .order_by(MovimientoInventario.fecha_hora.desc(), MovimientoInventario.id.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_usuario_by_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)
