"""Reglas de negocio de CU06 — Gestionar sucursales."""

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal

from .repository import CiudadesRepository, SucursalesRepository
from .schemas import CiudadCrear, SucursalActualizar, SucursalCrear


class SucursalNoEncontradaError(Exception):
    pass


class CiudadNoEncontradaError(Exception):
    """La ciudad indicada no existe."""


class NombreDuplicadoError(Exception):
    """Ya existe una sucursal con ese nombre en la misma ciudad."""


class CiudadNombreDuplicadoError(Exception):
    """Ya existe una ciudad con ese nombre (evita duplicados inconsistentes)."""


class CiudadesService:
    def __init__(self, db: Session):
        self._repo = CiudadesRepository(db)

    def listar(self, is_active: bool | None = None) -> list[Ciudad]:
        return self._repo.listar(is_active=is_active)

    def obtener(self, ciudad_id: int) -> Ciudad:
        ciudad = self._repo.get_by_id(ciudad_id)
        if ciudad is None:
            raise CiudadNoEncontradaError
        return ciudad

    def crear(self, datos: CiudadCrear) -> Ciudad:
        if self._repo.existe_nombre(datos.nombre):
            raise CiudadNombreDuplicadoError

        ciudad = Ciudad(
            nombre=datos.nombre,
            departamento=datos.departamento,
            is_active=datos.is_active,
        )
        return self._repo.crear(ciudad)

    def cambiar_estado(self, ciudad_id: int, activo: bool) -> Ciudad:
        ciudad = self.obtener(ciudad_id)
        ciudad.is_active = activo
        return self._repo.guardar(ciudad)


class SucursalesService:
    def __init__(self, db: Session):
        self._repo = SucursalesRepository(db)
        self._ciudades = CiudadesRepository(db)

    def listar(
        self, search: str | None, ciudad_id: int | None, is_active: bool | None
    ) -> list[Sucursal]:
        return self._repo.listar(search=search, ciudad_id=ciudad_id, is_active=is_active)

    def obtener(self, sucursal_id: int) -> Sucursal:
        sucursal = self._repo.get_by_id(sucursal_id)
        if sucursal is None:
            raise SucursalNoEncontradaError
        return sucursal

    def crear(self, datos: SucursalCrear) -> Sucursal:
        if self._ciudades.get_by_id(datos.ciudad_id) is None:
            raise CiudadNoEncontradaError

        if self._repo.existe_nombre_en_ciudad(datos.nombre, datos.ciudad_id):
            raise NombreDuplicadoError

        sucursal = Sucursal(
            nombre=datos.nombre,
            ciudad_id=datos.ciudad_id,
            direccion=datos.direccion,
            telefono=datos.telefono,
            is_active=datos.is_active,
        )
        return self._repo.crear(sucursal)

    def actualizar(self, sucursal_id: int, datos: SucursalActualizar) -> Sucursal:
        sucursal = self.obtener(sucursal_id)

        if self._ciudades.get_by_id(datos.ciudad_id) is None:
            raise CiudadNoEncontradaError

        if self._repo.existe_nombre_en_ciudad(
            datos.nombre, datos.ciudad_id, excluyendo_id=sucursal.id
        ):
            raise NombreDuplicadoError

        sucursal.nombre = datos.nombre
        sucursal.ciudad_id = datos.ciudad_id
        sucursal.direccion = datos.direccion
        sucursal.telefono = datos.telefono
        return self._repo.guardar(sucursal)

    def cambiar_estado(self, sucursal_id: int, activo: bool) -> Sucursal:
        sucursal = self.obtener(sucursal_id)
        sucursal.is_active = activo
        return self._repo.guardar(sucursal)
