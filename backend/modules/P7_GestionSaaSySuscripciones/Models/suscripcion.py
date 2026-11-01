"""Entidad Suscripción — Contrato de empresa con un plan SaaS.

Una Suscripción es la relación entre una Empresa y un Plan.
Define cuándo inicia, cuándo vence, y si está activa.

Multitenant: cada empresa tiene su propia suscripción(es).
"""

from datetime import datetime, timedelta

from sqlalchemy import Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Suscripcion(Base):
    __tablename__ = "suscripciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(Integer, ForeignKey("empresas.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("planes.id"), nullable=False)

    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_vencimiento: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    en_prueba: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fecha_fin_prueba: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Índices para búsquedas frecuentes (empresa, plan, vigencia)
    __table_args__ = (
        # Índice para consultas de suscripción actual de una empresa
        # (empresa + activa + no vencida)
    )
