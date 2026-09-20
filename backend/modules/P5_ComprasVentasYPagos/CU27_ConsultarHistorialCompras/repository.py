"""Acceso a datos de CU27 -- Consultar historial de compras (Cliente/Cajero).

Únicamente lecturas -- reutiliza Venta/VentaDetalle (CU22/CU24), Pago
(CU23/CU25), Usuario (CU01) y DevolucionCambio (CU26, solo lectura, nunca se
escribe desde aquí) tal cual existen. Ninguna tabla propia.
"""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P5_ComprasVentasYPagos.Models.devolucion import DevolucionCambio
from modules.P5_ComprasVentasYPagos.Models.pago import EstadoPago, Pago
from modules.P5_ComprasVentasYPagos.Models.venta import EstadoVenta, Venta


def _inicio_del_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.min, tzinfo=timezone.utc)


def _inicio_del_dia_siguiente(dia: date) -> datetime:
    return _inicio_del_dia(dia) + timedelta(days=1)


class VentaRepository:
    def __init__(self, db: Session):
        self.db = db

    def _filtrar_comun(self, stmt, desde: date | None, hasta: date | None, codigo_venta: str | None):
        """Fechas SIEMPRE inclusivas en ambos extremos -- comparación
        directa contra el rango de instantes de cada día (nunca se envuelve
        la columna en una función, para no perder el uso de su índice)."""
        if desde is not None:
            stmt = stmt.where(Venta.fecha_creacion >= _inicio_del_dia(desde))
        if hasta is not None:
            stmt = stmt.where(Venta.fecha_creacion < _inicio_del_dia_siguiente(hasta))
        if codigo_venta:
            stmt = stmt.where(Venta.codigo_venta.ilike(f"%{codigo_venta.strip()}%"))
        return stmt

    def listar_por_cliente(
        self, cliente_id: int, desde: date | None, hasta: date | None, codigo_venta: str | None
    ) -> list[Venta]:
        stmt = select(Venta).where(Venta.cliente_id == cliente_id, Venta.estado == EstadoVenta.PAGADA)
        stmt = self._filtrar_comun(stmt, desde, hasta, codigo_venta)
        stmt = stmt.order_by(Venta.fecha_creacion.desc(), Venta.id.desc())
        return list(self.db.execute(stmt).scalars().all())

    def listar_por_sucursal(
        self, sucursal_id: int, desde: date | None, hasta: date | None, codigo_venta: str | None
    ) -> list[Venta]:
        stmt = select(Venta).where(Venta.sucursal_id == sucursal_id, Venta.estado == EstadoVenta.PAGADA)
        stmt = self._filtrar_comun(stmt, desde, hasta, codigo_venta)
        stmt = stmt.order_by(Venta.fecha_creacion.desc(), Venta.id.desc())
        return list(self.db.execute(stmt).scalars().all())


class PagoRepository:
    def __init__(self, db: Session):
        self.db = db

    def mapa_pagado_por_ventas(self, venta_ids: list[int]) -> dict[int, Pago]:
        """Un Pago PAGADO por Venta -- solo uno puede llegar a ese estado
        (ver Models/pago.py), así que no hace falta desambiguar más de uno
        por venta_id."""
        if not venta_ids:
            return {}
        stmt = select(Pago).where(Pago.venta_id.in_(venta_ids), Pago.estado == EstadoPago.PAGADO)
        return {pago.venta_id: pago for pago in self.db.execute(stmt).scalars()}


class DevolucionLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def tipos_por_venta(self, venta_ids: list[int]) -> dict[int, set[str]]:
        """Qué TIPOS de operación postventa (CU26: DEVOLUCION y/o CAMBIO)
        tiene registrados cada Venta -- una consulta simple sobre las filas
        ya existentes de DevolucionCambio, nunca escribe nada aquí ni
        depende de cantidades (CU27 solo necesita saber SI hubo una
        devolución/cambio y de qué tipo(s), no cuánto)."""
        if not venta_ids:
            return {}
        stmt = select(DevolucionCambio.venta_id, DevolucionCambio.tipo).where(
            DevolucionCambio.venta_id.in_(venta_ids)
        )
        resultado: dict[int, set[str]] = {}
        for venta_id, tipo in self.db.execute(stmt).all():
            resultado.setdefault(venta_id, set()).add(tipo.value)
        return resultado


class UsuarioLecturaRepository:
    def __init__(self, db: Session):
        self.db = db

    def mapa_por_ids(self, usuario_ids: set[int]) -> dict[int, Usuario]:
        if not usuario_ids:
            return {}
        stmt = select(Usuario).where(Usuario.id.in_(usuario_ids))
        return {u.id: u for u in self.db.execute(stmt).scalars()}
