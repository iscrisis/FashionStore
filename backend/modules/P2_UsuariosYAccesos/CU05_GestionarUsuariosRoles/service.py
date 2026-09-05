"""Reglas de negocio de CU05 — Gestionar usuarios y roles."""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .repository import UsuariosRolesRepository
from .schemas import (
    ROLES_CON_PROVEEDOR,
    ROLES_CON_SUCURSAL,
    ROLES_INTERNOS,
    UsuarioActualizar,
    UsuarioCrear,
)


class UsuarioNoEncontradoError(Exception):
    pass


class CorreoDuplicadoError(Exception):
    pass


class RolNoAsignableError(Exception):
    """CLIENTE (CU02), ADMINISTRADOR (cuenta única) o un cambio de rol entre
    grupo "sucursal" y grupo "proveedor" (requeriría re-vincular la cuenta)."""


class SucursalNoEncontradaError(Exception):
    """La sucursal indicada no existe."""


class ProveedorNoEncontradoError(Exception):
    """El proveedor indicado no existe."""


class ProveedorYaVinculadoError(Exception):
    """Ese proveedor ya tiene una cuenta de acceso vinculada."""


class OperacionNoPermitidaError(Exception):
    """Auto-desactivación bloqueada."""


class UsuariosRolesService:
    def __init__(self, db: Session):
        self._repo = UsuariosRolesRepository(db)

    def listar(
        self, search: str | None, rol: RolUsuario | None, is_active: bool | None
    ) -> list[Usuario]:
        return self._repo.listar(search=search, rol=rol, is_active=is_active)

    def obtener(self, usuario_id: int) -> Usuario:
        usuario = self._repo.get_by_id(usuario_id)
        # El Administrador General queda fuera de CU05 por completo: no aparece,
        # no se edita, no se desactiva ni se reasigna de rol. Se comporta como si
        # no existiera para este caso de uso (igual que listar() en repository.py).
        if usuario is None or usuario.rol == RolUsuario.ADMINISTRADOR:
            raise UsuarioNoEncontradoError
        return usuario

    def crear(self, datos: UsuarioCrear) -> Usuario:
        if datos.rol not in ROLES_INTERNOS:
            raise RolNoAsignableError

        # El esquema (UsuarioCrear) ya garantiza cuál campo debe venir según el
        # rol; aquí solo se valida que el id recibido exista de verdad.
        if datos.sucursal_id is not None and self._repo.get_sucursal(datos.sucursal_id) is None:
            raise SucursalNoEncontradaError

        if datos.proveedor_id is not None:
            if self._repo.get_proveedor(datos.proveedor_id) is None:
                raise ProveedorNoEncontradoError
            if self._repo.proveedor_ya_vinculado(datos.proveedor_id):
                raise ProveedorYaVinculadoError

        if self._repo.get_by_correo(datos.correo) is not None:
            raise CorreoDuplicadoError

        usuario = Usuario(
            nombre=datos.nombre.strip(),
            correo=datos.correo.strip().lower(),
            password_hash=hash_password(datos.password),
            rol=datos.rol,
            is_active=datos.is_active,
            sucursal_id=datos.sucursal_id,
            proveedor_id=datos.proveedor_id,
        )
        return self._repo.crear(usuario)

    def actualizar_datos(self, usuario_id: int, datos: UsuarioActualizar) -> Usuario:
        usuario = self.obtener(usuario_id)

        existente = self._repo.get_by_correo(datos.correo.strip().lower())
        if existente is not None and existente.id != usuario.id:
            raise CorreoDuplicadoError

        # A diferencia de crear(), aquí el rol no viene en el payload: se usa
        # el rol ya guardado en el usuario para saber qué campo es obligatorio.
        if usuario.rol in ROLES_CON_SUCURSAL:
            if datos.sucursal_id is None or self._repo.get_sucursal(datos.sucursal_id) is None:
                raise SucursalNoEncontradaError
            usuario.sucursal_id = datos.sucursal_id
        elif usuario.rol in ROLES_CON_PROVEEDOR:
            if datos.proveedor_id is None or self._repo.get_proveedor(datos.proveedor_id) is None:
                raise ProveedorNoEncontradoError
            if self._repo.proveedor_ya_vinculado(datos.proveedor_id, excluyendo_usuario_id=usuario.id):
                raise ProveedorYaVinculadoError
            usuario.proveedor_id = datos.proveedor_id

        usuario.nombre = datos.nombre.strip()
        usuario.correo = datos.correo.strip().lower()
        return self._repo.guardar(usuario)

    def cambiar_rol(self, usuario_id: int, nuevo_rol: RolUsuario, actor: Usuario) -> Usuario:
        if nuevo_rol not in ROLES_INTERNOS:
            raise RolNoAsignableError

        usuario = self.obtener(usuario_id)

        # Cambiar entre el grupo "sucursal" y el grupo "proveedor" dejaría a la
        # cuenta sin el vínculo que su nuevo rol exige (este endpoint no recibe
        # sucursal_id/proveedor_id) — se rechaza; hay que editarlo con el otro
        # vínculo ya elegido, o recrear la cuenta.
        if (usuario.rol in ROLES_CON_SUCURSAL) != (nuevo_rol in ROLES_CON_SUCURSAL):
            raise RolNoAsignableError

        usuario.rol = nuevo_rol
        return self._repo.guardar(usuario)

    def cambiar_estado(self, usuario_id: int, activo: bool, actor: Usuario) -> Usuario:
        usuario = self.obtener(usuario_id)

        if not activo and usuario.id == actor.id:
            raise OperacionNoPermitidaError

        usuario.is_active = activo
        return self._repo.guardar(usuario)
