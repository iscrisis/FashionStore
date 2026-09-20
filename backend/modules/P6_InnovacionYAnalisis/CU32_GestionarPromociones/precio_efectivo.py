"""Precio efectivo -- fuente ÚNICA de verdad del precio vigente de un
Producto (CU32).

Reutilizado por CU11 (catálogo/detalle público), CU21 (carrito), CU22
(compra digital) y CU24 (venta presencial) -- ninguno de esos CU vuelve a
calcular el descuento por su cuenta ("no duplicar la fórmula de descuento en
múltiples CU"). CU23 (Stripe) y CU25 (pago presencial) NO lo necesitan: ya
cobran `Venta.total`, calculado por CU22/CU24 a partir de este mismo precio
en el momento de crear cada VentaDetalle -- ese valor queda congelado ahí
(histórico), CU26/CU27/CU31 tampoco lo vuelven a tocar.

SIEMPRE Decimal para el cálculo monetario (nunca float) -- el redondeo a 2
decimales usa ROUND_HALF_UP, mismo criterio ya usado por
app/integrations/stripe_client.py (_monto_a_unidad_minima).

Regla (única, sin excepciones): si el producto tiene una promoción ACTIVA
ahora mismo (activa=True, fecha_inicio <= hoy <= fecha_fin) -- por
construcción nunca hay más de una por producto en un mismo día, CU32 rechaza
los solapamientos al crear/editar --:
    precio_final = precio_base - (precio_base * porcentaje / 100)
Si no, `precio_final == precio_base` y `en_promocion=False`.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P6_InnovacionYAnalisis.Models.promocion import Promocion, promocion_productos


@dataclass(frozen=True)
class PrecioEfectivo:
    precio_base: Decimal
    precio_final: Decimal
    en_promocion: bool
    porcentaje_descuento: Decimal | None


def _redondear(monto: Decimal) -> Decimal:
    return monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calcular(precio_base: Decimal, porcentaje: Decimal | None) -> PrecioEfectivo:
    if porcentaje is None:
        return PrecioEfectivo(precio_base, precio_base, False, None)
    descuento = _redondear(precio_base * porcentaje / Decimal("100"))
    return PrecioEfectivo(precio_base, _redondear(precio_base - descuento), True, porcentaje)


def _porcentajes_activos_por_producto(
    db: Session, producto_ids: list[int], hoy: date
) -> dict[int, Decimal]:
    if not producto_ids:
        return {}
    stmt = (
        select(promocion_productos.c.producto_id, Promocion.porcentaje_descuento)
        .select_from(promocion_productos.join(Promocion, Promocion.id == promocion_productos.c.promocion_id))
        .where(
            promocion_productos.c.producto_id.in_(producto_ids),
            Promocion.activa.is_(True),
            Promocion.fecha_inicio <= hoy,
            Promocion.fecha_fin >= hoy,
        )
    )
    return dict(db.execute(stmt).all())


def obtener_precios_efectivos(db: Session, productos: list[Producto]) -> dict[int, PrecioEfectivo]:
    """UNA sola consulta para TODOS los productos dados -- pensado para
    listados (CU11 catálogo, CU21 carrito), nunca una consulta por
    producto."""
    hoy = date.today()
    porcentajes = _porcentajes_activos_por_producto(db, [p.id for p in productos], hoy)
    return {producto.id: _calcular(producto.precio_venta, porcentajes.get(producto.id)) for producto in productos}


def obtener_precio_efectivo(db: Session, producto: Producto) -> PrecioEfectivo:
    """Un único producto -- ver obtener_precios_efectivos para varios a la vez."""
    return obtener_precios_efectivos(db, [producto])[producto.id]
