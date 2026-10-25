"""Reglas de negocio de CU02 — Gestionar administrador de empresa."""

from sqlalchemy.orm import Session

from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from .repository import AdministradorEmpresaRepository
from .schemas import (
    AdministradorActualizar,
    ConsultarAdministradorOut,
    AdministradorOut,
    EmpresaOut,
)


class EmpresaNoEncontradaError(Exception):
    """La empresa solicitada no existe."""

    pass


class AdministradorNoEncontradoError(Exception):
    """No existe administrador para la empresa seleccionada."""

    pass


class AdministradorTieneOtroRolError(Exception):
    """El usuario encontrado no es ADMINISTRADOR (no debería ocurrir en CU02)."""

    pass


class CorreoDuplicadoError(Exception):
    """Ya existe otro usuario con ese correo."""

    pass


class TenantViolationError(Exception):
    """Intento de violar el aislamiento de tenants."""

    pass


class AdministradorEmpresaService:
    """Lógica de negocio para gestión de administrador de empresa."""

    def __init__(self, db: Session):
        self._repo = AdministradorEmpresaRepository(db)
        self._db = db

    def consultar_administrador(self, empresa_id: int) -> ConsultarAdministradorOut:
        """Consultar datos del administrador de una empresa.

        PRECONDICIÓN: El usuario autenticado es SUPERADMIN.

        Args:
            empresa_id: ID de la empresa cuyo administrador se consulta.

        Returns:
            ConsultarAdministradorOut con empresa + administrador.

        Raises:
            EmpresaNoEncontradaError: Si la empresa no existe.
            AdministradorNoEncontradoError: Si no existe administrador para la empresa.
            AdministradorTieneOtroRolError: Si el usuario encontrado no es ADMINISTRADOR.
        """
        # Validar que la empresa existe
        empresa = self._repo.obtener_empresa_por_id(empresa_id)
        if not empresa:
            raise EmpresaNoEncontradaError

        # Obtener el administrador de la empresa
        administrador = self._repo.obtener_administrador_por_empresa(empresa_id)
        if not administrador:
            raise AdministradorNoEncontradoError

        # Validación de integridad: el usuario debe ser ADMINISTRADOR
        if administrador.rol != RolUsuario.ADMINISTRADOR:
            raise AdministradorTieneOtroRolError

        return ConsultarAdministradorOut(
            empresa=EmpresaOut.model_validate(empresa),
            administrador=AdministradorOut.model_validate(administrador),
        )

    def actualizar_administrador(
        self,
        empresa_id: int,
        datos: AdministradorActualizar,
    ) -> ConsultarAdministradorOut:
        """Actualizar datos del administrador de una empresa.

        PRECONDICIÓN: El usuario autenticado es SUPERADMIN.

        RESTRICCIONES CRÍTICAS:
        - No se permite cambiar el rol (debe seguir siendo ADMINISTRADOR).
        - No se permite cambiar empresa_id (debe seguir siendo empresa_id inicial).
        - Se permite: nombre, correo, is_active.

        Args:
            empresa_id: ID de la empresa.
            datos: Datos a actualizar (nombre, correo, is_active).

        Returns:
            ConsultarAdministradorOut actualizado.

        Raises:
            EmpresaNoEncontradaError: Si la empresa no existe.
            AdministradorNoEncontradoError: Si no existe administrador para la empresa.
            CorreoDuplicadoError: Si el nuevo correo ya está en uso.
            TenantViolationError: Si se detecta intento de cambio de empresa_id.
        """
        # Validar que la empresa existe
        empresa = self._repo.obtener_empresa_por_id(empresa_id)
        if not empresa:
            raise EmpresaNoEncontradaError

        # Obtener el administrador actual
        administrador = self._repo.obtener_administrador_por_empresa(empresa_id)
        if not administrador:
            raise AdministradorNoEncontradoError

        # Validación de integridad del tenant
        if administrador.empresa_id != empresa_id:
            raise TenantViolationError

        # Validar que el usuario es ADMINISTRADOR
        if administrador.rol != RolUsuario.ADMINISTRADOR:
            raise AdministradorTieneOtroRolError

        # Validar que el nuevo correo no esté duplicado (excluyendo el administrador actual)
        if datos.correo.lower() != administrador.correo.lower():
            if self._repo.existe_correo_usuario(datos.correo, administrador.id):
                raise CorreoDuplicadoError

        # Actualizar los datos permitidos
        administrador_actualizado = self._repo.actualizar_administrador(
            administrador,
            nombre=datos.nombre,
            correo=datos.correo,
            is_active=datos.is_active,
        )

        # Validar nuevamente que la empresa_id se mantuvo
        if administrador_actualizado.empresa_id != empresa_id:
            # Esto nunca debería ocurrir, pero es una validación defensiva
            self._db.rollback()
            raise TenantViolationError

        return ConsultarAdministradorOut(
            empresa=EmpresaOut.model_validate(empresa),
            administrador=AdministradorOut.model_validate(administrador_actualizado),
        )
