"""Acceso a datos de CU20 -- Atender reserva de prendas (Encargado).

Reutiliza Reserva/ReservaDetalle (CU17), Producto (CU08), Usuario (CU02/05 --
cliente_id sin relationship() ORM, mismo patrón que ya documenta
P4_ReservasYAtencion/Models/reserva.py) y StockSucursal (CU14/15/16, columna
stock_reservado agregada por CU17) tal cual existen -- no crea ninguna tabla
nueva.

`with_for_update(of=<Entidad>)` sigue el mismo patrón ya usado por CU17 y
CU19 (ver sus repository.py): tanto ReservaDetalle (join a su
producto_variante) como StockSucursal tienen relationship(lazy="joined"), así
que restringir el FOR UPDATE a la tabla propia es obligatorio -- de lo
contrario Postgres intenta bloquear también las filas del JOIN (lado
"nullable" de un LEFT OUTER JOIN) y falla.

Cada transición de un detalle bloquea DOS filas, en este orden fijo (mismo
criterio que ya documentaba CU19 para reserva+stock, para evitar
interbloqueos): primero el ReservaDetalle mismo, después su Reserva
(cabecera) -- el segundo lock serializa el recálculo de `estado_general`
cuando dos detalles de LA MISMA reserva cambian de estado casi al mismo
tiempo (sin él, ambas transacciones podrían leer `reserva.detalles` antes de
que la otra confirme y una de las dos recalcularía con una foto vieja).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva, Reserva, ReservaDetalle


class ReservaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_por_sucursal(self, sucursal_id: int) -> list[Reserva]:
        """Sin lock -- solo lectura para armar el panel. Las transiciones de
        estado (preparar/confirmar/finalizar/enviar a caja) relockean la
        fila puntual que van a modificar vía ReservaDetalleRepository."""
        stmt = (
            select(Reserva)
            .where(Reserva.sucursal_id == sucursal_id)
            .options(selectinload(Reserva.detalles).selectinload(ReservaDetalle.producto_variante))
            .order_by(Reserva.fecha_reserva, Reserva.hora_inicio)
        )
        return list(self.db.execute(stmt).scalars().all())

    def listar_por_sucursal_y_estado_general(self, sucursal_id: int, estado: EstadoReserva) -> list[Reserva]:
        """Sin lock -- usado por el Cajero: cabeceras COMPLETAS (con
        `estado_general == estado`) de SU sucursal, agrupadas con todos sus
        detalles -- nunca una reserva todavía EN_ATENCION, aunque alguna de
        sus prendas ya esté LISTA_PARA_CAJA (ver
        AtenderReservaService.listar_pendientes_cajero: el filtrado de qué
        detalles mostrar de cada una sigue en el service)."""
        stmt = (
            select(Reserva)
            .where(Reserva.sucursal_id == sucursal_id, Reserva.estado_general == estado)
            .options(selectinload(Reserva.detalles).selectinload(ReservaDetalle.producto_variante))
            .order_by(Reserva.fecha_reserva, Reserva.hora_inicio)
        )
        return list(self.db.execute(stmt).scalars().all())

    def bloquear_por_id(self, reserva_id: int) -> Reserva | None:
        """SELECT ... FOR UPDATE sobre la cabecera -- ver docstring del
        módulo: serializa el recálculo de `estado_general` entre detalles
        hermanos que cambian de estado a la vez, y protege las transiciones
        propias de la cabecera (confirmar llegada, finalizar atención) de
        una doble ejecución concurrente. `detalles` viene precargado
        (selectinload) -- confirmar_llegada_reserva/finalizar_atencion
        necesitan revisar/mutar TODOS los detalles de la reserva."""
        stmt = (
            select(Reserva)
            .where(Reserva.id == reserva_id)
            .options(selectinload(Reserva.detalles).selectinload(ReservaDetalle.producto_variante))
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
        """SELECT ... FOR UPDATE: evita que dos peticiones (doble clic del
        mismo Encargado, u otro Encargado con acceso a la misma sucursal)
        cambien de estado el mismo detalle a la vez. `reserva` viene
        precargada (joinedload) -- toda transición necesita
        `detalle.reserva.sucursal_id` para autorizar."""
        stmt = (
            select(ReservaDetalle)
            .where(ReservaDetalle.id == detalle_id)
            .options(joinedload(ReservaDetalle.reserva))
            .with_for_update(of=ReservaDetalle)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def listar_por_sucursal_y_estado(self, sucursal_id: int, estado: EstadoReserva) -> list[ReservaDetalle]:
        """Sin lock -- usado por el Cajero (integración mínima de CU20):
        solo necesita ver los detalles LISTA_PARA_CAJA de SU sucursal, nunca
        el resto del flujo que sigue siendo exclusivo del Encargado."""
        stmt = (
            select(ReservaDetalle)
            .join(Reserva, ReservaDetalle.reserva_id == Reserva.id)
            .where(Reserva.sucursal_id == sucursal_id, ReservaDetalle.estado == estado)
            .options(joinedload(ReservaDetalle.reserva))
            .order_by(Reserva.fecha_reserva, Reserva.hora_inicio)
        )
        return list(self.db.execute(stmt).scalars().all())


class ProductoLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, producto_id: int) -> Producto | None:
        return self.db.get(Producto, producto_id)


class ClienteLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)


class StockSucursalRepository:
    def __init__(self, db: Session):
        self.db = db

    def bloquear_para_liberar(self, sucursal_id: int, variante_id: int) -> StockSucursal | None:
        stmt = (
            select(StockSucursal)
            .where(
                StockSucursal.sucursal_id == sucursal_id,
                StockSucursal.producto_variante_id == variante_id,
            )
            .with_for_update(of=StockSucursal)
        )
        return self.db.execute(stmt).scalar_one_or_none()
