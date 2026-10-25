"""Acceso a datos de Empresa y Usuario necesario para CU01."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario


class EmpresasRepository:
    """Repositorio para operaciones de persistencia de Empresa."""

    def __init__(self, db: Session):
        self.db = db

    def existe_nombre(self, nombre: str, excluyendo_id: int | None = None) -> bool:
        """Verificar si ya existe una empresa con ese nombre."""
        stmt = select(func.count()).select_from(Empresa).where(
            func.lower(Empresa.nombre) == nombre.strip().lower()
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Empresa.id != excluyendo_id)
        return self.db.execute(stmt).scalar_one() > 0

    def existe_slug(self, slug: str, excluyendo_id: int | None = None) -> bool:
        """Verificar si ya existe una empresa con ese slug."""
        stmt = select(func.count()).select_from(Empresa).where(
            func.lower(Empresa.slug) == slug.strip().lower()
        )
        if excluyendo_id is not None:
            stmt = stmt.where(Empresa.id != excluyendo_id)
        return self.db.execute(stmt).scalar_one() > 0

    def crear(self, empresa: Empresa) -> Empresa:
        """Crear y persistir una nueva empresa."""
        self.db.add(empresa)
        self.db.commit()
        self.db.refresh(empresa)
        return empresa

    def obtener_por_id(self, empresa_id: int) -> Empresa | None:
        """Obtener empresa por su ID."""
        return self.db.get(Empresa, empresa_id)

    def obtener_por_slug(self, slug: str) -> Empresa | None:
        """Obtener empresa por su slug."""
        stmt = select(Empresa).where(func.lower(Empresa.slug) == slug.strip().lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def existe_correo_usuario(self, correo: str) -> bool:
        """Verificar si ya existe un usuario con ese correo."""
        stmt = select(func.count()).select_from(Usuario).where(
            func.lower(Usuario.correo) == correo.strip().lower()
        )
        return self.db.execute(stmt).scalar_one() > 0

    def crear_usuario(self, usuario: Usuario) -> Usuario:
        """Crear y persistir un nuevo usuario administrador."""
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def listar_todas(self) -> list[Empresa]:
        """Listar todas las empresas de la plataforma."""
        stmt = select(Empresa).order_by(Empresa.created_at.desc())
        return self.db.execute(stmt).scalars().all()
