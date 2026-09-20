"""Entidades de Carrito, propias del paquete P5 -- Compras, ventas y pagos.

CU21 (usar carrito de compras) es el primer consumidor. Un Carrito representa
la intención de COMPRA DIGITAL de un Cliente -- NUNCA una reserva ni una
venta: agregar un producto aquí no crea Reserva, no crea Venta, no crea Pago,
y no toca StockSucursal (ni `cantidad` el físico, ni `stock_reservado` -- ver
CU21_UsarCarritoCompras/service.py, que solo LEE stock para validar
disponibilidad, nunca lo escribe). El carrito puede quedar guardado días sin
garantizar que el stock siga existiendo al momento de una compra real -- esa
validación final es responsabilidad de un CU posterior, fuera de este
alcance.

cliente_id es UNIQUE: cada Cliente tiene un único carrito, creado la primera
vez que agrega algo (ver CarritoRepository.obtener_o_crear) -- no existe el
concepto de "varios carritos" ni de "carrito abandonado" distinto del activo.

Cada fila de CarritoItem representa UNA unidad concreta de una variante
(Producto + Color + Talla) -- no existe columna `cantidad`: agregar la MISMA
variante otra vez NUNCA incrementa nada, crea una segunda fila independiente
(ver CarritoService.agregar_item), a propósito, para que el Cliente pueda
luego seleccionar solo una de las dos unidades si decide comprar nada más
esa. Por eso ya NO hay UniqueConstraint(carrito_id, producto_variante_id).

`seleccionado` es la única forma de marcar, por unidad, cuáles prendas se
considerarán para una compra futura (checkbox del carrito) -- no crea Venta
ni Pago (eso es de un CU posterior), solo se lee para calcular el subtotal
de lo seleccionado.

NO se guarda `precio_unitario` como dato persistido: el carrito siempre
muestra el precio ACTUAL de Producto.precio_venta al consultarse (ver
service.py) -- el precio definitivo de una compra se resuelve en un CU
posterior, fuera de este alcance.

cliente_id referencia a Usuario SOLO por columna, sin relationship() ORM --
mismo patrón ya usado por Reserva (P4) y RecepcionMercaderia/
MovimientoInventario (P1). producto_variante_id usa ON DELETE CASCADE por el
mismo motivo ya documentado en esos módulos: CU08 elimina físicamente una
ProductoVariante cuando el Administrador quita esa combinación talla/color de
un producto.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante


class Carrito(Base):
    __tablename__ = "carritos"
    __table_args__ = (UniqueConstraint("cliente_id", name="uq_carritos_cliente_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["CarritoItem"]] = relationship(
        back_populates="carrito", cascade="all, delete-orphan", order_by="CarritoItem.id"
    )


class CarritoItem(Base):
    __tablename__ = "carrito_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    carrito_id: Mapped[int] = mapped_column(ForeignKey("carritos.id", ondelete="CASCADE"), nullable=False)
    producto_variante_id: Mapped[int] = mapped_column(
        ForeignKey("producto_variantes.id", ondelete="CASCADE"), nullable=False
    )
    seleccionado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    fecha_agregado: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    carrito: Mapped[Carrito] = relationship(back_populates="items")
    producto_variante: Mapped[ProductoVariante] = relationship(lazy="joined")
