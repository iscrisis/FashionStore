"""Entidad Pago, propia del paquete P5 -- Compras, ventas y pagos.

CU23 (procesar pago electrónico) fue su primer consumidor -- Stripe Checkout
Hosted, modo TEST, sobre una Venta DIGITAL. CU25 (procesar pago presencial)
lo REUTILIZA tal cual para el mostrador (Cajero): mismo modelo, mismas
columnas de trazabilidad, sin crear un segundo sistema de pagos. Un Pago es
la trazabilidad de UN intento/registro de cobro sobre una Venta -- nunca la
Venta en sí, que sigue siendo la fuente de verdad de qué se compró y por
cuánto (ver Models/venta.py).

Una Venta puede tener VARIOS Pago a lo largo del tiempo (Stripe cancelado/
fallido, CU23 permite reintentar), pero SOLO uno puede terminar PAGADO: en
cuanto uno se confirma, la Venta pasa a PAGADA.

  - proveedor: STRIPE (CU23, Cliente/DIGITAL) o EFECTIVO/TARJETA/QR (CU25,
    Cajero/PRESENCIAL) -- funciona como "método de pago": el mismo campo ya
    distinguía "cómo se cobró", CU25 solo amplía sus valores posibles (misma
    migración ADD VALUE ya usada para tipo_venta/estado_venta).
  - stripe_checkout_session_id/stripe_payment_intent_id: SOLO tienen valor
    para proveedor == STRIPE -- por eso stripe_checkout_session_id es
    NULLABLE (CU25 la deja en NULL; sigue UNIQUE, Postgres permite múltiples
    NULL en una columna UNIQUE sin conflicto).
  - cajero_id: SOLO para pagos presenciales (CU25) -- quién lo registró en
    el mostrador, resuelto siempre de su token, nunca de un id que Angular
    envíe. NULL para STRIPE (lo confirma FastAPI solo, sin ningún actor
    humano de por medio).
  - monto_recibido/cambio: SOLO para proveedor == EFECTIVO -- lo que el
    Cliente entregó en el mostrador y el vuelto calculado
    (`cambio = monto_recibido - monto`). NULL para cualquier otro método.
  - tipo_tarjeta: SOLO para proveedor == TARJETA -- DEBITO o CREDITO. CU25
    NUNCA guarda número de tarjeta, CVC ni fecha de vencimiento (se cobra
    con un POS/datáfono físico externo, fuera de este sistema).
  - referencia: opcional, para TARJETA (número de autorización del POS) o
    QR (referencia de la transacción) -- nunca un dato sensible.
  - monto: SIEMPRE Venta.total en el momento de confirmar -- nunca un valor
    que envíe Angular.
  - estado: PENDIENTE (Stripe, sesión creada) -> PAGADO (confirmado) |
    CANCELADO | FALLIDO. CU25 SIEMPRE crea su Pago ya PAGADO -- un pago
    presencial se confirma en el momento mismo de registrarlo (efectivo/
    tarjeta/QR ya verificados por el Cajero en el mostrador), nunca queda
    "pendiente" a la espera de una confirmación externa asíncrona como
    Stripe.
  - fecha_confirmacion: SOLO se llena al pasar a PAGADO -- null en cualquier
    otro estado.

venta_id usa ON DELETE CASCADE por el mismo motivo ya documentado en
CarritoItem/ReservaDetalle: un Pago nunca puede sobrevivir a su Venta.
"""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P5_ComprasVentasYPagos.Models.venta import Venta


class ProveedorPago(str, enum.Enum):
    STRIPE = "STRIPE"
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    QR = "QR"


class EstadoPago(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    PAGADO = "PAGADO"
    CANCELADO = "CANCELADO"
    FALLIDO = "FALLIDO"


class TipoTarjeta(str, enum.Enum):
    """Solo aplica a Pago.proveedor == TARJETA (CU25)."""

    DEBITO = "DEBITO"
    CREDITO = "CREDITO"


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    proveedor: Mapped[ProveedorPago] = mapped_column(
        SAEnum(ProveedorPago, name="proveedor_pago"), nullable=False, default=ProveedorPago.STRIPE
    )
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estado: Mapped[EstadoPago] = mapped_column(
        SAEnum(EstadoPago, name="estado_pago"), nullable=False, default=EstadoPago.PENDIENTE
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_confirmacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # CU25 -- Procesar pago presencial (Cajero). Todo NULL para proveedor == STRIPE.
    cajero_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    monto_recibido: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cambio: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    tipo_tarjeta: Mapped[TipoTarjeta | None] = mapped_column(
        SAEnum(TipoTarjeta, name="tipo_tarjeta"), nullable=True
    )
    referencia: Mapped[str | None] = mapped_column(String(120), nullable=True)

    venta: Mapped[Venta] = relationship(lazy="joined")
