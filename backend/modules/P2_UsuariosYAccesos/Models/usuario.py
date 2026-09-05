"""Entidad Usuario, compartida por todo el paquete P2 — Usuarios y accesos.

CU01 (iniciar sesión) es el primer consumidor. CU02, CU03, CU04 y CU05 reutilizarán
este mismo modelo — no debe duplicarse por caso de uso.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .rol import RolUsuario


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        SAEnum(RolUsuario, name="rol_usuario"), nullable=False, default=RolUsuario.CLIENTE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
