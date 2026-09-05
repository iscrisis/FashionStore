"""Entidad Usuario, compartida por todo el paquete P2 — Usuarios y accesos.

CU01 (iniciar sesión) es el primer consumidor. CU02, CU03, CU04 y CU05 reutilizarán
este mismo modelo — no debe duplicarse por caso de uso.

sucursal_id referencia a Sucursal (modules/P1_SucursalesYCatalogos/Models), no la
duplica: un empleado interno (ENCARGADO_SUCURSAL/CAJERO) queda ligado a su
sucursal, y a través de ella a su ciudad (Usuario → Sucursal → Ciudad). Permite
NULL porque ADMINISTRADOR y CLIENTE no pertenecen a ninguna sucursal.

proveedor_id referencia a Proveedor (modules/P1_SucursalesYCatalogos/Models),
tampoco lo duplica: una cuenta con rol PROVEEDOR queda ligada a SU proveedor
(Usuario → Proveedor), nunca a una sucursal. Es unique porque cada proveedor
tiene una única cuenta de acceso.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal

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
    sucursal_id: Mapped[int | None] = mapped_column(ForeignKey("sucursales.id"), nullable=True)
    proveedor_id: Mapped[int | None] = mapped_column(
        ForeignKey("proveedores.id"), unique=True, nullable=True
    )

    sucursal: Mapped[Sucursal | None] = relationship(lazy="joined")
    proveedor: Mapped[Proveedor | None] = relationship(lazy="joined")
