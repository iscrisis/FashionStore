"""Acceso a datos de CU31 -- Emitir comprobante de venta (Cliente/Cajero).

Únicamente lecturas -- CU31 no muta ninguna entidad, solo arma una proyección
de solo lectura sobre Venta/VentaDetalle (CU22/CU24), Pago (CU23/CU25),
Producto (CU08) y Usuario (CU01) tal cual existen. Ninguna tabla propia, ver
__init__.py.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P5_ComprasVentasYPagos.Models.pago import EstadoPago, Pago
from modules.P5_ComprasVentasYPagos.Models.venta import Venta, VentaDetalle


class VentaRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, venta_id: int) -> Venta | None:
        """Solo lectura -- CU31 nunca bloquea (FOR UPDATE) ni muta la Venta."""
        stmt = (
            select(Venta)
            .where(Venta.id == venta_id)
            .options(selectinload(Venta.detalles).selectinload(VentaDetalle.producto_variante))
        )
        return self.db.execute(stmt).scalar_one_or_none()


class PagoRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_pagado_por_venta(self, venta_id: int) -> Pago | None:
        stmt = (
            select(Pago)
            .where(Pago.venta_id == venta_id, Pago.estado == EstadoPago.PAGADO)
            .order_by(Pago.id.desc())
        )
        return self.db.execute(stmt).scalars().first()


class ProductoLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_ids(self, producto_ids: set[int]) -> dict[int, Producto]:
        """Sin filtrar por `is_active` -- igual que CU26: un comprobante es
        de una compra YA REALIZADA, un producto desactivado después de
        venderse debe seguir apareciendo en su propio comprobante."""
        if not producto_ids:
            return {}
        stmt = select(Producto).where(Producto.id.in_(producto_ids))
        return {p.id: p for p in self.db.execute(stmt).scalars()}


class UsuarioLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)
