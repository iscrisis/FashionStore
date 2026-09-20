"""Acceso a datos de CU25 -- Procesar pago presencial (Cajero).

Reutiliza Venta/VentaDetalle (CU22/CU24), StockSucursal (CU14/15/16) y
Reserva/ReservaDetalle (CU17-CU20) tal cual existen -- ESCRIBE en las tres
(a diferencia de CU21/22/23/24, que solo las leían) porque confirmar un pago
presencial es, precisamente, el momento en que se materializan sus efectos:
la Venta pasa a PAGADA, el stock se descuenta, y (si corresponde) la Reserva
pasa a ATENDIDA. La tabla propia de este módulo es Pago, ya creada por CU23.

Todos los `bloquear_*` usan SELECT ... FOR UPDATE a propósito -- mismo
criterio ya usado en CU17/CU22/CU23: la Venta se bloquea PRIMERO (cabecera
antes que stock/reserva), así dos confirmaciones concurrentes de la MISMA
Venta (doble clic, doble pestaña) nunca duplican el descuento de stock ni
el cambio de estado de la reserva (ver PagoPresencialService.confirmar_pago).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P4_ReservasYAtencion.Models.reserva import Reserva, ReservaDetalle
from modules.P5_ComprasVentasYPagos.Models.pago import Pago
from modules.P5_ComprasVentasYPagos.Models.venta import Venta, VentaDetalle


class VentaRepository:
    def __init__(self, db: Session):
        self.db = db

    def bloquear_por_id(self, venta_id: int) -> Venta | None:
        stmt = (
            select(Venta)
            .where(Venta.id == venta_id)
            .options(selectinload(Venta.detalles).selectinload(VentaDetalle.producto_variante))
            .with_for_update(of=Venta)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def refrescar(self, venta: Venta) -> None:
        self.db.refresh(venta)


class StockSucursalRepository:
    def __init__(self, db: Session):
        self.db = db

    def bloquear_filas(self, sucursal_id: int, variante_ids: list[int]) -> dict[int, StockSucursal]:
        if not variante_ids:
            return {}
        stmt = (
            select(StockSucursal)
            .where(
                StockSucursal.sucursal_id == sucursal_id,
                StockSucursal.producto_variante_id.in_(variante_ids),
            )
            .with_for_update(of=StockSucursal)
        )
        return {fila.producto_variante_id: fila for fila in self.db.execute(stmt).scalars()}


class ReservaRepository:
    def __init__(self, db: Session):
        self.db = db

    def bloquear_por_id(self, reserva_id: int) -> Reserva | None:
        stmt = (
            select(Reserva)
            .where(Reserva.id == reserva_id)
            .options(selectinload(Reserva.detalles))
            .with_for_update(of=Reserva)
        )
        return self.db.execute(stmt).scalar_one_or_none()


class PagoRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, pago: Pago) -> Pago:
        """Único commit: Pago + Venta (PAGADA) + stock + (si corresponde)
        Reserva (ATENDIDA) quedan consistentes juntos, o nada de eso se
        aplica -- ver PagoPresencialService.confirmar_pago."""
        self.db.add(pago)
        self.db.commit()
        self.db.refresh(pago)
        return pago
