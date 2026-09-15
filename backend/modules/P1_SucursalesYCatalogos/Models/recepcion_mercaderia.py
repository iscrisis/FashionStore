"""Entidad RecepcionMercaderia, compartida por el paquete P1 — Sucursales y catálogo.

CU15 (registrar recepción de mercadería) es el primer consumidor. Deja
trazabilidad de que un ENCARGADO_SUCURSAL recibió físicamente mercadería de
un Proveedor en SU sucursal -- quién, cuándo, de qué proveedor y en qué
sucursal -- sin duplicar esos datos (solo referencias por id).

usuario_id referencia a Usuario (modules/P2_UsuariosYAccesos/Models) SOLO por
columna, sin relationship() ORM: ningún modelo de este paquete (P1) importa
modelos de P2 hoy (es P2 quien importa de P1, ver usuario.py), y romper esa
dirección no aporta nada aquí -- el usuario que registró se resuelve en la
capa de servicio de CU15 a partir del actor ya autenticado.

No reemplaza StockSucursal: cada recepción confirmada suma cantidad a
StockSucursal a través de sus detalles (ver DetalleRecepcionMercaderia), pero
la recepción en sí queda guardada como historial permanente aunque el stock
luego se ajuste manualmente desde CU14.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from .detalle_recepcion_mercaderia import DetalleRecepcionMercaderia
from .proveedor import Proveedor
from .sucursal import Sucursal


class RecepcionMercaderia(Base):
    __tablename__ = "recepciones_mercaderia"

    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), nullable=False)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    observacion: Mapped[str | None] = mapped_column(String(500), nullable=True)

    proveedor: Mapped[Proveedor] = relationship(lazy="joined")
    sucursal: Mapped[Sucursal] = relationship(lazy="joined")
    detalles: Mapped[list[DetalleRecepcionMercaderia]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by=DetalleRecepcionMercaderia.id
    )
