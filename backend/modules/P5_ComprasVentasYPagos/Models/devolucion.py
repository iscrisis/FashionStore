"""Entidad DevolucionCambio, propia del paquete P5 -- Compras, ventas y pagos.

CU26 (registrar devolución o cambio) es su único consumidor. Trazabilidad de
UNA operación del Cajero sobre UNA línea (`VentaDetalle`) de una Venta ya
PAGADA -- nunca sobre la Venta completa: el Cajero puede devolver/cambiar
prenda por prenda, y cada unidad comprada solo puede consumirse una vez entre
todas sus operaciones (ver `cantidad_operada_por_detalle` en repository.py,
que sirve de tope tanto a una devolución como a un cambio posteriores sobre
esa misma línea -- así nunca se puede devolver ni cambiar más unidades que
las realmente compradas, sea cual sea la combinación de operaciones).

No existe un estado "pendiente": a diferencia de Pago (que sí puede quedar
PENDIENTE mientras Stripe confirma), una fila de este modelo SOLO se crea
cuando la operación ya se aplicó por completo -- stock actualizado y, si
corresponde, reembolso registrado, todo en la misma transacción (ver
CU26_RegistrarDevolucionCambio/service.py). Por eso no lleva columna
`estado` propia: su sola existencia ya es la confirmación.

tipo distingue las dos operaciones de CU26, mutuamente excluyentes:
  - DEVOLUCION: la prenda vuelve a StockSucursal.cantidad de la sucursal de
    la venta; `variante_nueva_id` queda NULL. Lleva reembolso (ver abajo).
  - CAMBIO: la prenda original vuelve al stock (igual que una devolución) y
    la nueva variante se descuenta -- ambos efectos, una sola fila. Nunca
    lleva reembolso: CU26 solo permite cambiar por otra variante del MISMO
    producto (mismo precio_venta por construcción, ver service.py), así que
    nunca hay diferencia de dinero que devolver ni cobrar.

variante_original_id/variante_nueva_id -- ON DELETE CASCADE por el mismo
motivo ya documentado en VentaDetalle: CU08 elimina físicamente una
ProductoVariante cuando el Administrador quita esa combinación talla/color de
un producto.

motivo/observacion -- SOLO para DEVOLUCION (NULL en CAMBIO). `observacion`
solo es obligatoria, a nivel de servicio, cuando `motivo == OTRO` -- ver
CU26_RegistrarDevolucionCambio/service.py.

Reembolso -- SOLO para DEVOLUCION (los cuatro campos quedan NULL en CAMBIO):
  - metodo_reembolso reutiliza el enum `ProveedorPago` ya definido por
    Pago (STRIPE/EFECTIVO/TARJETA/QR) -- es SIEMPRE el mismo método con el
    que se pagó la venta (ver Pago.proveedor), nunca uno que el Cajero elija
    libremente: no tiene sentido reembolsar por un medio distinto al que
    pagó el Cliente.
  - monto_reembolso: SIEMPRE `VentaDetalle.precio_unitario * cantidad` --
    calculado por FastAPI, nunca un monto que Angular envíe.
  - estado_reembolso: REGISTRADO (EFECTIVO ya entregado en mano, o
    TARJETA/QR que el Cajero ya procesó fuera del sistema, en el POS/app
    bancaria) o COMPLETADO (Stripe confirmó el refund real en modo TEST).
  - stripe_refund_id: SOLO cuando metodo_reembolso == STRIPE.

cajero_id/sucursal_id -- SIEMPRE resueltos del actor autenticado (JWT) y de
`Venta.sucursal_id`, nunca de un valor que Angular envíe (ver router.py).

venta_id/venta_detalle_id usan ON DELETE CASCADE por el mismo motivo ya
documentado en VentaDetalle: una Venta o un VentaDetalle nunca deberían
borrarse físicamente, pero si ocurriera, no debe arrastrarse la Venta ya
registrada como huérfana.
"""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P5_ComprasVentasYPagos.Models.pago import ProveedorPago
from modules.P5_ComprasVentasYPagos.Models.venta import Venta, VentaDetalle


class TipoOperacionDevolucion(str, enum.Enum):
    DEVOLUCION = "DEVOLUCION"
    CAMBIO = "CAMBIO"


class MotivoDevolucion(str, enum.Enum):
    TALLA = "TALLA"
    DEFECTO = "DEFECTO"
    PRODUCTO_INCORRECTO = "PRODUCTO_INCORRECTO"
    OTRO = "OTRO"


class EstadoReembolso(str, enum.Enum):
    REGISTRADO = "REGISTRADO"
    COMPLETADO = "COMPLETADO"


class DevolucionCambio(Base):
    __tablename__ = "devoluciones_cambios"
    __table_args__ = (CheckConstraint("cantidad > 0", name="ck_devolucion_cambio_cantidad_positiva"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    venta_detalle_id: Mapped[int] = mapped_column(
        ForeignKey("venta_detalles.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[TipoOperacionDevolucion] = mapped_column(
        SAEnum(TipoOperacionDevolucion, name="tipo_operacion_devolucion"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    variante_original_id: Mapped[int] = mapped_column(
        ForeignKey("producto_variantes.id", ondelete="CASCADE"), nullable=False
    )
    variante_nueva_id: Mapped[int | None] = mapped_column(
        ForeignKey("producto_variantes.id", ondelete="CASCADE"), nullable=True
    )
    motivo: Mapped[MotivoDevolucion | None] = mapped_column(
        SAEnum(MotivoDevolucion, name="motivo_devolucion"), nullable=True
    )
    observacion: Mapped[str | None] = mapped_column(String(300), nullable=True)

    monto_reembolso: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    metodo_reembolso: Mapped[ProveedorPago | None] = mapped_column(
        SAEnum(ProveedorPago, name="proveedor_pago"), nullable=True
    )
    estado_reembolso: Mapped[EstadoReembolso | None] = mapped_column(
        SAEnum(EstadoReembolso, name="estado_reembolso"), nullable=True
    )
    stripe_refund_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    cajero_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    venta: Mapped[Venta] = relationship(lazy="joined")
    venta_detalle: Mapped[VentaDetalle] = relationship(lazy="joined")
    variante_original: Mapped[ProductoVariante] = relationship(
        foreign_keys=[variante_original_id], lazy="joined"
    )
    variante_nueva: Mapped[ProductoVariante | None] = relationship(
        foreign_keys=[variante_nueva_id], lazy="joined"
    )
    sucursal: Mapped[Sucursal] = relationship(lazy="joined")
