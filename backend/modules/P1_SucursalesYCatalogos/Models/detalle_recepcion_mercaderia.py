"""Entidad DetalleRecepcionMercaderia, compartida por el paquete P1 — Sucursales y catálogo.

Cada fila es una variante (talla+color) recibida dentro de una
RecepcionMercaderia (CU15), con la cantidad física que llegó. No duplica
"Negro"/"M"/nombre de producto como texto: referencia ProductoVariante (CU08)
por id, igual que ya hace StockSucursal.

producto_variante_id usa ON DELETE CASCADE por el mismo motivo documentado en
stock_sucursal.py: CU08 elimina físicamente una ProductoVariante cuando el
Administrador quita esa combinación talla/color de un producto; sin este
CASCADE esa operación fallaría por esta referencia.
"""

from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from .producto_variante import ProductoVariante


class DetalleRecepcionMercaderia(Base):
    __tablename__ = "detalles_recepcion_mercaderia"
    __table_args__ = (
        CheckConstraint("cantidad_recibida > 0", name="ck_detalle_recepcion_cantidad_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recepcion_id: Mapped[int] = mapped_column(
        ForeignKey("recepciones_mercaderia.id", ondelete="CASCADE"), nullable=False
    )
    producto_variante_id: Mapped[int] = mapped_column(
        ForeignKey("producto_variantes.id", ondelete="CASCADE"), nullable=False
    )
    cantidad_recibida: Mapped[int] = mapped_column(Integer, nullable=False)

    producto_variante: Mapped[ProductoVariante] = relationship(lazy="joined")
