"""Acceso a datos de CU19 -- Cancelar reserva (Cliente).

Reutiliza Reserva/ReservaDetalle (CU17), Producto (CU08) y StockSucursal
(CU14/15/16, ya escrita en su columna stock_reservado por CU17) tal cual
existen -- no crea ninguna tabla nueva.

Los locks (`with_for_update`) siguen el mismo orden que ya documentaba este
archivo antes de separar cabecera/detalle: primero la Reserva (cabecera),
después cada ReservaDetalle que se vaya a cancelar, y por último la fila de
StockSucursal que libera cada uno -- mismo orden en todos los casos para
evitar interbloqueos. `of=<Entidad>` es obligatorio aquí porque
ReservaDetalle, Reserva y StockSucursal tienen relationship(lazy="joined")
-- sin restringir el FOR UPDATE a la tabla propia, Postgres intentaría
bloquear también las filas del JOIN (lado "nullable" de un LEFT OUTER JOIN)
y falla.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P4_ReservasYAtencion.Models.reserva import Reserva, ReservaDetalle


class ReservaRepository:
    def __init__(self, db: Session):
        self.db = db

    def bloquear_por_id(self, reserva_id: int) -> Reserva | None:
        """SELECT ... FOR UPDATE sobre la cabecera -- primer lock de toda
        cancelación (de un detalle o de la reserva entera), sin este lock
        dos cancelaciones concurrentes sobre la MISMA reserva podrían pisar
        el recálculo de `estado_general` una de la otra."""
        stmt = (
            select(Reserva)
            .where(Reserva.id == reserva_id)
            .options(selectinload(Reserva.detalles))
            .with_for_update(of=Reserva)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def guardar(self) -> None:
        self.db.commit()

    def refrescar(self, reserva: Reserva) -> None:
        self.db.refresh(reserva)


class ReservaDetalleRepository:
    def __init__(self, db: Session):
        self.db = db

    def bloquear_por_id(self, detalle_id: int) -> ReservaDetalle | None:
        """SELECT ... FOR UPDATE sobre el detalle mismo: sin este lock, dos
        solicitudes de cancelación concurrentes para el MISMO detalle
        podrían leer ambas estado=PENDIENTE antes de que la primera
        confirme, y las dos liberarían stock_reservado -- un doble
        descuento. `reserva` viene precargada (joinedload): cancelar
        necesita `detalle.reserva.sucursal_id` para liberar el stock
        correcto."""
        stmt = (
            select(ReservaDetalle)
            .where(ReservaDetalle.id == detalle_id)
            .options(joinedload(ReservaDetalle.reserva))
            .with_for_update(of=ReservaDetalle)
        )
        return self.db.execute(stmt).scalar_one_or_none()


class ProductoLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, producto_id: int) -> Producto | None:
        return self.db.get(Producto, producto_id)


class StockSucursalRepository:
    def __init__(self, db: Session):
        self.db = db

    def bloquear_para_liberar(self, sucursal_id: int, variante_id: int) -> StockSucursal | None:
        """SELECT ... FOR UPDATE sobre la fila de stock -- misma razón que
        CrearReservaService.crear: evita pisar una escritura concurrente
        sobre stock_reservado (otra cancelación o una reserva nueva) para
        esta misma sucursal+variante."""
        stmt = (
            select(StockSucursal)
            .where(
                StockSucursal.sucursal_id == sucursal_id,
                StockSucursal.producto_variante_id == variante_id,
            )
            .with_for_update(of=StockSucursal)
        )
        return self.db.execute(stmt).scalar_one_or_none()
