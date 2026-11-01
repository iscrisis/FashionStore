"""Entidad Plan — Definición de planes SaaS disponibles en FashionStore.

Un Plan es una modalidad de suscripción que la plataforma ofrece.
Define capacidades, límites y precio.

Cada empresa puede contratar un plan (relación en tabla suscripciones).
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Plan(Base):
    __tablename__ = "planes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)

    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    limite_sucursales: Mapped[int] = mapped_column(nullable=False, default=1)
    limite_usuarios: Mapped[int] = mapped_column(nullable=False, default=5)

    # Funcionalidades configurables por plan
    gestion_productos: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    gestion_ventas: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reservas: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    operacion_offline: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reportes_convencionales: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reportes_generativos_ia: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
