"""Reglas de negocio de CU01 — Registrar empresa contratante."""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from modules.P7_GestionSaaSySuscripciones.Models.empresa import Empresa
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from .repository import EmpresasRepository
from .schemas import EmpresaCrear, RegistroEmpresaOut


class EmpresaNombreDuplicadoError(Exception):
    """Ya existe una empresa con ese nombre."""

    pass


class EmpresaSlugDuplicadoError(Exception):
    """Ya existe una empresa con ese slug."""

    pass


class CorreoAdministradorDuplicadoError(Exception):
    """Ya existe un usuario con ese correo de administrador."""

    pass


class EmpresaNoEncontradaError(Exception):
    """La empresa solicitada no existe."""

    pass


class EmpresasService:
    """Lógica de negocio para gestión de empresas."""

    def __init__(self, db: Session):
        self._repo = EmpresasRepository(db)
        self._db = db

    def crear(self, datos: EmpresaCrear) -> RegistroEmpresaOut:
        """Crear una nueva empresa contratante con su administrador.

        Valida que nombre, slug y correo sean únicos. La creación es atómica:
        si falla la creación del administrador, se hace rollback de la empresa.

        Args:
            datos: Datos de la empresa y administrador a crear.

        Returns:
            RegistroEmpresaOut con datos de empresa y administrador creados.

        Raises:
            EmpresaNombreDuplicadoError: Si el nombre ya existe.
            EmpresaSlugDuplicadoError: Si el slug ya existe.
            CorreoAdministradorDuplicadoError: Si el correo ya existe.
        """
        if self._repo.existe_nombre(datos.nombre):
            raise EmpresaNombreDuplicadoError

        if self._repo.existe_slug(datos.slug):
            raise EmpresaSlugDuplicadoError

        if self._repo.existe_correo_usuario(datos.correo_admin):
            raise CorreoAdministradorDuplicadoError

        # Crear empresa
        empresa = Empresa(
            nombre=datos.nombre,
            slug=datos.slug,
            razon_social=datos.razon_social,
            correo=datos.correo,
            telefono=datos.telefono,
            is_active=True,
        )
        empresa = self._repo.crear(empresa)

        # Crear usuario administrador vinculado a la empresa (atómico)
        try:
            administrador = Usuario(
                nombre=datos.nombre_admin,
                correo=datos.correo_admin,
                password_hash=hash_password(datos.password),
                rol=RolUsuario.ADMINISTRADOR,
                empresa_id=empresa.id,
                is_active=True,
            )
            administrador = self._repo.crear_usuario(administrador)
        except Exception as e:
            # Rollback si falla creación del administrador
            self._db.rollback()
            raise e

        return RegistroEmpresaOut(empresa=empresa, administrador=administrador)

    def listar(self) -> list[Empresa]:
        """Listar todas las empresas de la plataforma (solo SUPERADMIN).

        Returns:
            Lista de todas las empresas.
        """
        return self._repo.listar_todas()

    def obtener_por_slug(self, slug: str) -> Empresa:
        """Obtener empresa por su slug.

        Args:
            slug: Identificador de la empresa.

        Returns:
            Empresa encontrada.

        Raises:
            EmpresaNoEncontradaError: Si la empresa no existe.
        """
        empresa = self._repo.obtener_por_slug(slug)
        if empresa is None:
            raise EmpresaNoEncontradaError
        return empresa
