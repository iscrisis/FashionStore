"""Reglas de negocio de CU07 -- Consultar sucursales (público).

Sin autenticación: Invitado o Cliente lo consulta sin iniciar sesión. Solo
lee lo que CU06 ya publicó como activo -- no administra nada.
"""

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal

from .repository import SucursalesPublicoRepository


class SucursalNoEncontradaError(Exception):
    pass


class SucursalesPublicoService:
    def __init__(self, db: Session):
        self._repo = SucursalesPublicoRepository(db)

    def listar_ciudades(self) -> list[Ciudad]:
        return self._repo.listar_ciudades_activas()

    def listar_sucursales(self, ciudad_id: int | None = None) -> list[Sucursal]:
        return self._repo.listar_sucursales_activas(ciudad_id=ciudad_id)

    def obtener_sucursal(self, sucursal_id: int) -> Sucursal:
        sucursal = self._repo.obtener_sucursal_activa(sucursal_id)
        if sucursal is None:
            raise SucursalNoEncontradaError
        return sucursal
