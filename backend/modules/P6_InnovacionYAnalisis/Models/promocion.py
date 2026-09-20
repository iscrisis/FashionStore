"""Entidad Promocion, propia del paquete P6 -- Innovación y análisis.

CU32 (gestionar promociones) es su único consumidor. Una promoción es un
descuento PORCENTUAL sobre uno o varios Producto -- nunca sobre
ProductoVariante (todas las variantes de un producto reciben el mismo
descuento mientras esté vigente, ver CU32_GestionarPromociones/__init__.py).
MVP: solo porcentual, nunca cupones, códigos, 2x1, descuento fijo en Bs,
por sucursal, por talla/color, ni acumulación.

precio_venta del Producto NUNCA se modifica -- esta tabla solo guarda la
promoción en sí (porcentaje + vigencia); el precio final se CALCULA aparte
en cada consulta (ver CU32_GestionarPromociones/precio_efectivo.py), nunca
se persiste. Cuando la promoción termina, el precio vuelve solo a
Producto.precio_venta porque nunca dejó de ser ese: nada que revertir.

`activa` es la única bandera persistida -- el ESTADO visible
(PROGRAMADA/ACTIVA/FINALIZADA/DESACTIVADA) se deriva en el momento
comparando `fecha_inicio`/`fecha_fin` contra la fecha actual (ver
CU32_GestionarPromociones/service.py) -- no hay cron ni un campo `estado`
guardado que pueda desincronizarse.

No se elimina físicamente ninguna promoción que ya tuvo vigencia -- solo se
puede "desactivar" (`activa = False`), nunca hay un DELETE en este módulo
(ver CU32_GestionarPromociones/service.py: no existe ningún método que borre
una fila de esta tabla).

`promocion_productos` es una tabla de asociación PURA (sin datos propios),
mismo patrón ya usado por `producto_tallas`/`producto_colores` (CU08, P1) --
sin clase de modelo dedicada, ver Models/producto_talla.py. producto_id NO
usa ON DELETE CASCADE hacia Producto a propósito: CU08 no elimina
físicamente un Producto (solo lo desactiva, `is_active`), así que esta fila
de asociación nunca queda huérfana por ese lado.
"""

import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P1_SucursalesYCatalogos.Models.producto import Producto

promocion_productos = Table(
    "promocion_productos",
    Base.metadata,
    Column("promocion_id", ForeignKey("promociones.id", ondelete="CASCADE"), primary_key=True),
    Column("producto_id", ForeignKey("productos.id"), primary_key=True),
)


class EstadoPromocion(str, enum.Enum):
    """Derivado, NUNCA persistido -- ver
    CU32_GestionarPromociones/service.py:_calcular_estado."""

    PROGRAMADA = "PROGRAMADA"
    ACTIVA = "ACTIVA"
    FINALIZADA = "FINALIZADA"
    DESACTIVADA = "DESACTIVADA"


class Promocion(Base):
    __tablename__ = "promociones"
    __table_args__ = (
        CheckConstraint(
            "porcentaje_descuento > 0 AND porcentaje_descuento < 100",
            name="ck_promocion_porcentaje_rango",
        ),
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_promocion_fechas_orden"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    porcentaje_descuento: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    productos: Mapped[list[Producto]] = relationship(
        secondary=promocion_productos, lazy="selectin", order_by=Producto.nombre
    )
