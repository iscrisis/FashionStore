"""Entidades de Venta, propias del paquete P5 -- Compras, ventas y pagos.

CU22 (realizar compra digital) es el primer consumidor. Una Venta representa
una COMPRA real del Cliente -- a diferencia de Carrito (CU21, intención pura,
nunca toca stock), crear una Venta es el momento en que el Cliente confirma
qué prendas quiere comprar y en qué sucursal las retirará. Aun así, CU22
sigue sin tocar StockSucursal (ni `cantidad` el físico, ni `stock_reservado`
-- ver CU22_RealizarCompraDigital/service.py, que solo LEE stock para
validar disponibilidad): reservar/descontar stock por una compra pendiente
de pago queda fuera de este alcance, es responsabilidad de un CU posterior
(CU23, aprobar/rechazar pago).

Venta (cabecera) -- quién, dónde y cuánto:
  - codigo_venta: identificador visible para el Cliente (ej. "VT-00001") --
    el `id` interno de Postgres NUNCA se expone como "número de compra" en
    ningún contrato de salida (mismo criterio que Reserva.codigo_reserva).
  - cliente_id/sucursal_id: el Cliente elige la sucursal de retiro (una
    sola, para TODA la compra -- CU22 no reparte una compra entre varias
    sucursales ni implementa envío a domicilio), el backend valida que
    exista, esté activa y pueda cubrir TODAS las variantes/cantidades
    seleccionadas antes de crear la Venta.
  - tipo: DIGITAL (CU22, compra iniciada desde el carrito web/futuro
    Flutter, con retiro en sucursal) o PRESENCIAL (CU24, el Cajero la arma
    en el mostrador -- venta directa o desde una reserva LISTA_PARA_CAJA).
    PRESENCIAL se agregó ampliando este mismo enum vía migración (mismo
    patrón ya usado para EstadoVenta.PAGADA), sin crear una tabla aparte --
    exactamente como ya anticipaba este docstring antes de CU24.
  - estado: CU22/CU24 SIEMPRE crean la Venta en PENDIENTE_PAGO. CU23
    (procesar pago electrónico) agrega PAGADA -- se llega ahí SOLO cuando
    FastAPI verificó directamente contra Stripe que el pago se completó
    (nunca porque Angular lo diga, ver
    CU23_ProcesarPagoElectronico/service.py). Un pago cancelado o fallido
    NO mueve este estado: la Venta se queda en PENDIENTE_PAGO para permitir
    reintentar (ver Models/pago.py). CU24 (presencial) también deja la
    Venta en PENDIENTE_PAGO -- confirmar el pago en el mostrador es
    responsabilidad de un CU25 futuro, fuera de este alcance.
  - total: SIEMPRE la suma de los `subtotal` de sus VentaDetalle, calculada
    por FastAPI en el momento de confirmar -- nunca un total que envíe
    Angular. CU23 vuelve a usar este mismo `total` (nunca un monto que
    Angular le pase) como el monto exacto que se cobra en Stripe.
  - cliente_id: NULLABLE -- una venta DIGITAL (CU22) o PRESENCIAL desde
    reserva (CU24) siempre tiene un Cliente dueño, pero una venta
    PRESENCIAL DIRECTA (Cliente sin cuenta, compra de mostrador) no exige
    registrar ninguno (ver CU24_RegistrarVentaPresencial/service.py).
  - cajero_id: quién registró la venta -- NULL para una Venta DIGITAL
    (CU22, la crea el propio Cliente autenticado, no hay Cajero de por
    medio); para PRESENCIAL (CU24) es SIEMPRE el Cajero autenticado que la
    arma, resuelto de su token, nunca de un id que Angular envíe.
  - origen: NULL para DIGITAL (no aplica); DIRECTA o RESERVA para
    PRESENCIAL (CU24) -- ver OrigenVenta.
  - reserva_id: NULL salvo que `origen == RESERVA` -- la Reserva
    LISTA_PARA_CAJA (CU17-CU20) de la que salieron las prendas de esta
    Venta. ON DELETE SET NULL: una Reserva no debería borrarse nunca
    físicamente, pero si ocurriera, no debe arrastrarse la Venta ya
    registrada. CU24 NUNCA cambia el estado de la Reserva ni de sus
    detalles al crear la Venta (sigue LISTA_PARA_CAJA hasta que un CU25
    futuro confirme el pago) -- ver CU24_RegistrarVentaPresencial/service.py.

VentaDetalle -- una prenda dentro de esa compra:
  - producto_variante_id + cantidad: igual que Reserva/CarritoItem (talla +
    color, CU08).
  - precio_unitario/subtotal: a diferencia de Carrito (que NUNCA guarda
    precio, siempre muestra el actual), VentaDetalle SÍ lo guarda -- es el
    precio de Producto.precio_venta en el momento exacto de confirmar la
    compra. Si el precio del producto cambia después, esta compra conserva
    el precio original con el que se pagó (o se pagará).
  - carrito_item_id: referencia al CarritoItem (CU21) del que salió esta
    línea -- nullable y ON DELETE SET NULL (un item de carrito puede dejar
    de existir por otras razones sin invalidar la Venta ya creada). Es la
    única forma en que CU23 sabe, al confirmar el pago, CUÁLES filas exactas
    del carrito borrar (las que formaron parte de ESTA Venta) sin tocar
    ninguna otra -- ni las no seleccionadas, ni una unidad nueva de la misma
    variante que el Cliente haya agregado después de confirmar la compra.

cliente_id referencia a Usuario SOLO por columna, sin relationship() ORM --
mismo patrón ya usado por Reserva (P4) y Carrito (P5): el Cliente dueño de
la venta se resuelve en la capa de servicio de CU22 a partir del actor ya
autenticado, nunca por join.

producto_variante_id usa ON DELETE CASCADE por el mismo motivo ya
documentado en Reserva/CarritoItem: CU08 elimina físicamente una
ProductoVariante cuando el Administrador quita esa combinación talla/color
de un producto. venta_id también usa ON DELETE CASCADE: una cabecera nunca
puede quedar con detalles huérfanos ni un detalle sin su cabecera.
"""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal


class TipoVenta(str, enum.Enum):
    DIGITAL = "DIGITAL"
    PRESENCIAL = "PRESENCIAL"


class EstadoVenta(str, enum.Enum):
    PENDIENTE_PAGO = "PENDIENTE_PAGO"
    PAGADA = "PAGADA"


class OrigenVenta(str, enum.Enum):
    """Solo aplica a Venta.tipo == PRESENCIAL (CU24) -- NULL para DIGITAL."""

    DIRECTA = "DIRECTA"
    RESERVA = "RESERVA"


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_venta: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), nullable=False)
    tipo: Mapped[TipoVenta] = mapped_column(SAEnum(TipoVenta, name="tipo_venta"), nullable=False)
    estado: Mapped[EstadoVenta] = mapped_column(
        SAEnum(EstadoVenta, name="estado_venta"), nullable=False, default=EstadoVenta.PENDIENTE_PAGO
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # CU24 -- Registrar venta presencial (Cajero). NULL para DIGITAL.
    cajero_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    origen: Mapped[OrigenVenta | None] = mapped_column(SAEnum(OrigenVenta, name="origen_venta"), nullable=True)
    reserva_id: Mapped[int | None] = mapped_column(
        ForeignKey("reservas.id", ondelete="SET NULL"), nullable=True
    )

    sucursal: Mapped[Sucursal] = relationship(lazy="joined")
    # order_by por id: los detalles se muestran siempre en el orden en que se
    # confirmaron, igual que Reserva.detalles.
    detalles: Mapped[list["VentaDetalle"]] = relationship(
        back_populates="venta", cascade="all, delete-orphan", order_by="VentaDetalle.id"
    )


class VentaDetalle(Base):
    """Una prenda dentro de una Venta -- variante + cantidad + el precio
    EXACTO con el que se confirmó la compra (ver docstring del módulo)."""

    __tablename__ = "venta_detalles"
    __table_args__ = (CheckConstraint("cantidad > 0", name="ck_venta_detalle_cantidad_positiva"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    producto_variante_id: Mapped[int] = mapped_column(
        ForeignKey("producto_variantes.id", ondelete="CASCADE"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    carrito_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("carrito_items.id", ondelete="SET NULL"), nullable=True
    )

    venta: Mapped[Venta] = relationship(back_populates="detalles")
    producto_variante: Mapped[ProductoVariante] = relationship(lazy="joined")
