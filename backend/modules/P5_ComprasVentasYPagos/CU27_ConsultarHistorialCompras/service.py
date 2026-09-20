"""Reglas de negocio de CU27 -- Consultar historial de compras (Cliente/Cajero).

cliente_id/sucursal_id llegan SIEMPRE resueltos desde el actor autenticado
(JWT, ver router.py) -- nunca desde un valor que Angular pueda enviar: un
Cliente solo ve sus propias compras, un Cajero solo las de SU sucursal (sin
importar qué Cajero las vendió -- el historial sirve para atención
posterior y devoluciones, CU26).

Solo se listan ventas PAGADA -- nunca PENDIENTE_PAGO ni una reserva
RS-XXXXX suelta (CU27 lista Venta, no Reserva). Una venta presencial directa
de mostrador sin `cliente_id` (CU24) nunca aparece en el historial de NINGÚN
Cliente, solo en el de la sucursal que la vendió.

`tiene_postventa`/`leyenda_postventa` son campos CALCULADOS, nunca
guardados -- se derivan en el momento de los TIPOS de operación que CU26 ya
registró para esa Venta (DevolucionCambio.tipo: DEVOLUCION y/o CAMBIO),
nunca de cuánto se devolvió/cambió:
  - sin ninguna fila -> `tiene_postventa=False`, `leyenda_postventa=None`
    (pestaña "Pagadas").
  - solo DEVOLUCION -> "Devolución realizada".
  - solo CAMBIO -> "Cambio realizado".
  - ambos tipos -> "Operación postventa registrada" (mensaje único, nunca
    varios badges).
`Venta.estado` en la base sigue siendo SIEMPRE "PAGADA" -- CU26 nunca lo
cambia (ver Models/devolucion.py) y CU27 tampoco inventa un estado nuevo
("DEVUELTA"/"CAMBIADA") para mostrarlo: la pestaña "Pagadas"/"Postventa"/
"Todas" del Cajero se arma en el FRONTEND filtrando `tiene_postventa` sobre
la MISMA lista, sin un endpoint ni un estado por pestaña.
"""

from datetime import date

from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P5_ComprasVentasYPagos.Models.venta import Venta

from .repository import DevolucionLecturaRepository, PagoRepository, UsuarioLecturaRepository, VentaRepository
from .schemas import SucursalHistorialOut, VentaHistorialOut


class RangoFechaInvalidoError(Exception):
    """`desde` es posterior a `hasta` -- rango vacío por definición."""


class SucursalCajeroNoDefinidaError(Exception):
    """El Cajero autenticado no tiene sucursal_id."""


def _leyenda_postventa(tipos: set[str]) -> str | None:
    if not tipos:
        return None
    if tipos == {"DEVOLUCION"}:
        return "Devolución realizada"
    if tipos == {"CAMBIO"}:
        return "Cambio realizado"
    return "Operación postventa registrada"


class HistorialComprasService:
    def __init__(self, db: Session):
        self._ventas = VentaRepository(db)
        self._pagos = PagoRepository(db)
        self._devoluciones = DevolucionLecturaRepository(db)
        self._usuarios = UsuarioLecturaRepository(db)

    @staticmethod
    def _validar_rango(desde: date | None, hasta: date | None) -> None:
        if desde is not None and hasta is not None and desde > hasta:
            raise RangoFechaInvalidoError

    def listar_mias(
        self, cliente: Usuario, desde: date | None, hasta: date | None, codigo_venta: str | None
    ) -> list[VentaHistorialOut]:
        self._validar_rango(desde, hasta)
        ventas = self._ventas.listar_por_cliente(cliente.id, desde, hasta, codigo_venta)
        return self._a_salida(ventas)

    def listar_sucursal(
        self, cajero: Usuario, desde: date | None, hasta: date | None, codigo_venta: str | None
    ) -> list[VentaHistorialOut]:
        if cajero.sucursal_id is None:
            raise SucursalCajeroNoDefinidaError
        self._validar_rango(desde, hasta)
        ventas = self._ventas.listar_por_sucursal(cajero.sucursal_id, desde, hasta, codigo_venta)
        return self._a_salida(ventas)

    def _a_salida(self, ventas: list[Venta]) -> list[VentaHistorialOut]:
        if not ventas:
            return []

        venta_ids = [v.id for v in ventas]
        pagos = self._pagos.mapa_pagado_por_ventas(venta_ids)
        tipos_por_venta = self._devoluciones.tipos_por_venta(venta_ids)

        cliente_ids = {v.cliente_id for v in ventas if v.cliente_id is not None}
        clientes = self._usuarios.mapa_por_ids(cliente_ids)

        salida: list[VentaHistorialOut] = []
        for venta in ventas:
            pago = pagos.get(venta.id)
            if pago is None:
                # Defensivo -- una Venta PAGADA siempre debería tener un
                # Pago PAGADO (CU23/CU25 los crean juntos); se omite en vez
                # de reventar el listado completo por una fila inconsistente.
                continue

            tipos = tipos_por_venta.get(venta.id, set())
            cliente = clientes.get(venta.cliente_id) if venta.cliente_id is not None else None

            salida.append(
                VentaHistorialOut(
                    venta_id=venta.id,
                    codigo_venta=venta.codigo_venta,
                    fecha=venta.fecha_creacion,
                    sucursal=SucursalHistorialOut(
                        id=venta.sucursal.id, nombre=venta.sucursal.nombre, ciudad=venta.sucursal.ciudad.nombre
                    ),
                    cliente_nombre=cliente.nombre if cliente is not None else None,
                    tipo=venta.tipo.value,
                    metodo_pago=pago.proveedor.value,
                    total=venta.total,
                    tiene_postventa=bool(tipos),
                    leyenda_postventa=_leyenda_postventa(tipos),
                )
            )
        return salida
