"""Acceso a datos de CU24 -- Registrar venta presencial (Cajero).

Reutiliza ProductoVariante/Producto (CU08), StockSucursal (CU14/15/16, en
SOLO LECTURA -- CU24 nunca escribe ninguna de sus columnas, ver service.py),
Reserva/ReservaDetalle (CU17-CU20, también en SOLO LECTURA -- CU24 nunca
cambia su estado) y Usuario (para el nombre del Cliente de una reserva). La
única tabla propia de este módulo es Venta/VentaDetalle, ya creada por CU22.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P4_ReservasYAtencion.Models.reserva import Reserva, ReservaDetalle
from modules.P5_ComprasVentasYPagos.Models.venta import EstadoVenta, Venta, VentaDetalle


class ProductoVarianteLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar_activas_por_nombre_producto(self, nombre: str) -> list[ProductoVariante]:
        stmt = (
            select(ProductoVariante)
            .join(Producto, ProductoVariante.producto_id == Producto.id)
            .where(
                Producto.is_active.is_(True),
                ProductoVariante.is_active.is_(True),
                Producto.nombre.ilike(f"%{nombre}%"),
            )
            .order_by(Producto.nombre)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_activas_by_ids(self, variante_ids: list[int]) -> dict[int, ProductoVariante]:
        if not variante_ids:
            return {}
        stmt = select(ProductoVariante).where(
            ProductoVariante.id.in_(variante_ids), ProductoVariante.is_active.is_(True)
        )
        return {v.id: v for v in self.db.execute(stmt).scalars()}


class ProductoLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_activos_by_ids(self, producto_ids: set[int]) -> dict[int, Producto]:
        if not producto_ids:
            return {}
        stmt = select(Producto).where(Producto.id.in_(producto_ids), Producto.is_active.is_(True))
        return {p.id: p for p in self.db.execute(stmt).scalars()}


class StockSucursalRepository:
    def __init__(self, db: Session):
        self.db = db

    def disponible_por_variantes(self, sucursal_id: int, variante_ids: list[int]) -> dict[int, int]:
        """SELECT puro, sin FOR UPDATE: CU24 solo valida disponibilidad,
        nunca escribe stock (eso queda para un CU25 futuro, después del
        pago)."""
        if not variante_ids:
            return {}
        stmt = select(
            StockSucursal.producto_variante_id, (StockSucursal.cantidad - StockSucursal.stock_reservado)
        ).where(
            StockSucursal.sucursal_id == sucursal_id,
            StockSucursal.producto_variante_id.in_(variante_ids),
        )
        return dict(self.db.execute(stmt).all())


class ReservaLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, reserva_id: int) -> Reserva | None:
        """Solo lectura -- CU24 nunca bloquea (FOR UPDATE) ni muta la
        Reserva: sigue LISTA_PARA_CAJA hasta que CU25 confirme el pago."""
        stmt = (
            select(Reserva)
            .where(Reserva.id == reserva_id)
            .options(selectinload(Reserva.detalles).selectinload(ReservaDetalle.producto_variante))
        )
        return self.db.execute(stmt).scalar_one_or_none()


class UsuarioLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)


class VentaRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, venta: Venta) -> Venta:
        """Mismo patrón ya usado por VentaRepository.crear (CU22/CU23):
        genera el `codigo_venta` a partir del id definitivo, con un
        placeholder único mientras tanto (NOT NULL en la base, se reemplaza
        antes de confirmar). Un único commit deja cabecera + detalles +
        código definitivo consistentes."""
        venta.codigo_venta = uuid.uuid4().hex[:20]
        self.db.add(venta)
        self.db.flush()
        venta.codigo_venta = f"VT-{venta.id:05d}"
        self.db.commit()
        self.db.refresh(venta)
        return venta

    def obtener_pendiente_por_reserva(self, reserva_id: int) -> Venta | None:
        """Evita duplicar una Venta PENDIENTE_PAGO para la misma reserva --
        si ya existe una, "cargar venta" la reutiliza en vez de crear otra
        (ver service.py)."""
        stmt = (
            select(Venta)
            .where(Venta.reserva_id == reserva_id, Venta.estado == EstadoVenta.PENDIENTE_PAGO)
            .options(selectinload(Venta.detalles).selectinload(VentaDetalle.producto_variante))
            .order_by(Venta.id.desc())
        )
        return self.db.execute(stmt).scalars().first()
