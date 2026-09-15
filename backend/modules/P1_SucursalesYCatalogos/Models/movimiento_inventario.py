"""Entidad MovimientoInventario, compartida por el paquete P1 — Sucursales y catálogo.

CU16 (registrar movimientos de inventario) es el primer consumidor. Deja
trazabilidad de un AJUSTE manual y justificado que un ENCARGADO_SUCURSAL hizo
sobre el stock de SU sucursal -- quién, cuándo, qué variante, cuánto cambió y
por qué -- sin duplicar esos datos (solo referencias por id).

NO es para recepción de proveedor: eso sigue siendo CU15 (RecepcionMercaderia),
un flujo completamente independiente con su propia trazabilidad. CU16 es para
correcciones (unidades dañadas, pérdidas, diferencias de conteo físico).

usuario_id referencia a Usuario (modules/P2_UsuariosYAccesos/Models) SOLO por
columna, sin relationship() ORM -- mismo motivo ya documentado en
recepcion_mercaderia.py: ningún modelo de este paquete (P1) importa modelos
de P2, y el usuario que registró se resuelve en la capa de servicio de CU16 a
partir del actor ya autenticado.

stock_anterior/stock_resultante quedan guardados en la fila (no se recalculan
después) para que el historial siga siendo exacto aunque StockSucursal vuelva
a cambiar más adelante por otro movimiento u otra recepción.

producto_variante_id usa ON DELETE CASCADE por el mismo motivo ya documentado
en stock_sucursal.py y detalle_recepcion_mercaderia.py: CU08 elimina
físicamente una ProductoVariante cuando el Administrador quita esa
combinación talla/color de un producto.
"""

import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from .producto_variante import ProductoVariante
from .sucursal import Sucursal


class TipoMovimientoInventario(str, enum.Enum):
    AJUSTE_POSITIVO = "AJUSTE_POSITIVO"
    AJUSTE_NEGATIVO = "AJUSTE_NEGATIVO"


class MovimientoInventario(Base):
    __tablename__ = "movimientos_inventario"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_movimiento_inventario_cantidad_positiva"),
        CheckConstraint(
            "stock_anterior >= 0 AND stock_resultante >= 0",
            name="ck_movimiento_inventario_stock_no_negativo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), nullable=False)
    producto_variante_id: Mapped[int] = mapped_column(
        ForeignKey("producto_variantes.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    tipo: Mapped[TipoMovimientoInventario] = mapped_column(
        SAEnum(TipoMovimientoInventario, name="tipo_movimiento_inventario"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str] = mapped_column(String(300), nullable=False)
    stock_anterior: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_resultante: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sucursal: Mapped[Sucursal] = relationship(lazy="joined")
    producto_variante: Mapped[ProductoVariante] = relationship(lazy="joined")
