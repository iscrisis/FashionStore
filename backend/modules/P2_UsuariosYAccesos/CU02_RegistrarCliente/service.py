"""Reglas de negocio de CU02 -- Registrar cliente (público).

El rol CLIENTE se asigna aquí, siempre, sin excepción -- nunca se lee de lo
que envía el cliente (RegistroClienteRequest ni siquiera tiene un campo
`rol`, ver schemas.py). Así un visitante no puede registrarse como
ADMINISTRADOR, ENCARGADO_SUCURSAL, CAJERO ni PROVEEDOR manipulando el
request; esos roles internos siguen siendo exclusivos de CU05. Reutiliza
hash_password (app.core.security), la misma función que ya usan CU01 y CU05
-- no duplica autenticación ni emite JWT (eso sigue siendo solo CU01).
"""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .repository import RegistroClienteRepository
from .schemas import RegistroClienteRequest


class CorreoYaRegistradoError(Exception):
    pass


class RegistroClienteService:
    def __init__(self, db: Session):
        self._repo = RegistroClienteRepository(db)

    def registrar(self, datos: RegistroClienteRequest) -> Usuario:
        if self._repo.existe_correo(datos.correo):
            raise CorreoYaRegistradoError

        usuario = Usuario(
            nombre=datos.nombre,
            correo=datos.correo,
            telefono=datos.telefono,
            password_hash=hash_password(datos.password),
            rol=RolUsuario.CLIENTE,
            is_active=True,
        )
        return self._repo.crear(usuario)
