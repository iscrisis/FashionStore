"""Entidad Temporada, compartida por todo el paquete P1 — Sucursales y catálogo.

CU10 (gestionar temporadas y colecciones) es el primer consumidor.

Multitenant: cada temporada pertenece a una empresa (cambio de GLOBAL a POR_EMPRESA
para coherencia arquitectónica con Colección, que es per-empresa).
Temporada 1 ---- N Colección, donde ambas pertenecen a la misma empresa.
"""

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa


class Temporada(Base):
    __tablename__ = "temporadas"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_temporada_empresa_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    empresa: Mapped[Empresa] = relationship(lazy="joined")
