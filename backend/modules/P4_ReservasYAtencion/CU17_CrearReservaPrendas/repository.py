"""Acceso a datos de CU17 -- Crear reserva de prendas (Cliente).

Reutiliza Sucursal (CU06), ProductoVariante (CU08) y StockSucursal (fuente
real de existencias, ya escrita por CU14/CU15/CU16) tal cual existen. Las
tablas propias de este módulo son Reserva (cabecera) y ReservaDetalle.

CU17 SÍ escribe en StockSucursal, pero solo en su columna `stock_reservado`
(nunca en `cantidad`, el stock físico -- ver Models/stock_sucursal.py): al
crear una reserva incrementa `stock_reservado` en la misma fila que ya
administra el Encargado, para que el stock realmente disponible
(`cantidad - stock_reservado`) baje sin tocar el físico.

`bloquear_para_reservar` usa SELECT ... FOR UPDATE a propósito: sin ese lock,
dos clientes podrían leer al mismo tiempo la misma última unidad disponible y
ambos terminar reservándola -- con el lock, el segundo espera a que el primero
confirme o aborte su transacción antes de leer el stock_reservado ya
actualizado (ver CrearReservaService.crear).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P4_ReservasYAtencion.Models.reserva import Reserva, ReservaDetalle


class SucursalLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_activa_by_id(self, sucursal_id: int) -> Sucursal | None:
        stmt = select(Sucursal).where(Sucursal.id == sucursal_id, Sucursal.is_active.is_(True))
        return self.db.execute(stmt).scalar_one_or_none()


class ProductoVarianteLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_variante_activa_by_id(self, variante_id: int) -> ProductoVariante | None:
        variante = self.db.get(ProductoVariante, variante_id)
        if variante is None or not variante.is_active:
            return None
        return variante

    def get_producto_activo(self, producto_id: int) -> Producto | None:
        producto = self.db.get(Producto, producto_id)
        if producto is None or not producto.is_active:
            return None
        return producto


class StockSucursalRepository:
    def __init__(self, db: Session):
        self.db = db

    def bloquear_para_reservar(self, sucursal_id: int, variante_id: int) -> StockSucursal | None:
        """SELECT ... FOR UPDATE: bloquea la fila de stock de esa
        sucursal+variante hasta que termine (commit o rollback) la
        transacción actual -- ver CrearReservaService.crear, que hace la
        validación de disponibilidad y el incremento de stock_reservado
        sobre esta misma fila ya bloqueada, dentro de la misma transacción.
        None si nunca se cargó stock para esa combinación (disponible = 0)."""
        # of=StockSucursal a propósito: StockSucursal.sucursal/.producto_variante
        # son relationship(lazy="joined") -- sin restringir el FOR UPDATE a esta
        # tabla, Postgres intentaría bloquear también las filas ya traídas por
        # ese JOIN (sucursales/producto_variantes, del lado "nullable" de un
        # LEFT OUTER JOIN) y falla con "FOR UPDATE cannot be applied to the
        # nullable side of an outer join". Solo la fila de stock necesita
        # bloquearse.
        stmt = (
            select(StockSucursal)
            .where(
                StockSucursal.sucursal_id == sucursal_id,
                StockSucursal.producto_variante_id == variante_id,
            )
            .with_for_update(of=StockSucursal)
        )
        return self.db.execute(stmt).scalar_one_or_none()


class ReservaRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, reserva: Reserva) -> Reserva:
        """Inserta la cabecera (con sus detalles ya asignados vía
        `reserva.detalles`, cascada por la relationship) y genera su
        `codigo_reserva` a partir del id definitivo -- por eso hace flush
        ANTES de fijar el código real: sin id todavía no hay nada que
        formatear. `codigo_reserva` es NOT NULL en la base, así que el
        primer INSERT necesita algún valor no nulo -- se usa un placeholder
        aleatorio (único, nunca colisiona con otra transacción concurrente)
        que el propio flush descarta al reemplazarlo por el código real
        antes de confirmar: nadie llega a ver ese valor temporal, ni
        siquiera otra transacción (no está commiteado). Un único commit deja
        cabecera + detalle(s) + código definitivo consistentes."""
        reserva.codigo_reserva = uuid.uuid4().hex[:20]
        self.db.add(reserva)
        self.db.flush()
        reserva.codigo_reserva = f"RS-{reserva.id:05d}"
        self.db.commit()
        self.db.refresh(reserva)
        return reserva

    def listar_por_cliente(self, cliente_id: int) -> list[Reserva]:
        stmt = (
            select(Reserva)
            .where(Reserva.cliente_id == cliente_id)
            .options(selectinload(Reserva.detalles).selectinload(ReservaDetalle.producto_variante))
            .order_by(Reserva.fecha_creacion.desc(), Reserva.id.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def listar_por_cliente_y_sucursal(self, cliente_id: int, sucursal_id: int) -> list[Reserva]:
        """Sin filtrar por estado_general en SQL a propósito: el service
        (listar_compatibles) primero corre expirar_vencidas sobre el
        resultado -- una reserva PENDIENTE en la base cuyo bloque horario ya
        pasó debe vencer ANTES de decidir si sigue siendo "compatible", no
        quedar afuera (ni adentro) por un estado todavía sin actualizar."""
        stmt = (
            select(Reserva)
            .where(Reserva.cliente_id == cliente_id, Reserva.sucursal_id == sucursal_id)
            .options(selectinload(Reserva.detalles).selectinload(ReservaDetalle.producto_variante))
            .order_by(Reserva.fecha_creacion.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def bloquear_por_id(self, reserva_id: int) -> Reserva | None:
        """SELECT ... FOR UPDATE sobre la cabecera -- agregar_detalle la
        bloquea antes de leer su estado_general y antes de mutar su
        colección de detalles, para que dos intentos concurrentes de agregar
        una prenda a la MISMA reserva nunca pisen el recálculo de
        estado_general ni dupliquen un detalle por una carrera de lecturas."""
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
