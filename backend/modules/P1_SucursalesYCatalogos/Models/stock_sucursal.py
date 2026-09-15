"""Entidad StockSucursal -- cantidad disponible de una ProductoVariante en una Sucursal.

Es la fuente REAL de existencias que un futuro CU12 (Consultar disponibilidad
por sucursal) consumirá en solo lectura: Producto + Color + Talla + Ciudad ->
Sucursales -> Stock real. Esta tabla no lo implementa todavía, solo deja los
datos.

No pertenece al Producto general ni a Ciudad ni a Usuario: una fila combina
Sucursal (CU06) + ProductoVariante (CU08, talla+color ya generada), sin
duplicar ninguna de esas dos entidades. La restricción de unicidad evita dos
filas de stock para la misma sucursal+variante -- se actualiza la cantidad
existente en su lugar (ver CU14_ConsultarInventario).

producto_variante_id usa ON DELETE CASCADE porque CU08 elimina físicamente una
ProductoVariante cuando el Administrador quita esa combinación talla/color de
un producto (ver Producto.variantes, cascade="all, delete-orphan"); sin este
CASCADE esa operación fallaría por la referencia desde stock.
"""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from .producto_variante import ProductoVariante
from .sucursal import Sucursal


class StockSucursal(Base):
    __tablename__ = "stock_sucursal"
    __table_args__ = (
        UniqueConstraint("sucursal_id", "producto_variante_id"),
        CheckConstraint("cantidad >= 0", name="ck_stock_sucursal_cantidad_no_negativa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), nullable=False)
    producto_variante_id: Mapped[int] = mapped_column(
        ForeignKey("producto_variantes.id", ondelete="CASCADE"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sucursal: Mapped[Sucursal] = relationship(lazy="joined")
    producto_variante: Mapped[ProductoVariante] = relationship(lazy="joined")
