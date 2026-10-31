"""Reglas de negocio de CU06 — Gestionar sucursales."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P7_GestionSaaSySuscripciones.CU03_AsociarUsuariosYSucursalesEmpresa.service import (
    AsociacionesEmpresaService,
)

from .repository import CiudadesRepository, SucursalesRepository
from .schemas import CiudadCrear, SucursalActualizar, SucursalCrear


class _SucursalConCiudad:
    """Wrapper que expone Sucursal con Ciudad cargada para Pydantic."""
    def __init__(self, sucursal: Sucursal, ciudad: Ciudad | None):
        self.id = sucursal.id
        self.empresa_id = sucursal.empresa_id
        self.nombre = sucursal.nombre
        self.ciudad_id = sucursal.ciudad_id
        self.direccion = sucursal.direccion
        self.telefono = sucursal.telefono
        self.is_active = sucursal.is_active
        self.ciudad = ciudad


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

    def eliminar(self, ciudad_id: int) -> None:
        ciudad = self.obtener(ciudad_id)
        self._repo.eliminar(ciudad)


class SucursalesService:
    def __init__(self, db: Session):
        self._db = db
        self._repo = SucursalesRepository(db)
        self._ciudades = CiudadesRepository(db)

    def _get_ciudad_for_sucursal(self, sucursal: Sucursal) -> Ciudad | None:
        """Obtiene la Ciudad de una Sucursal por ciudad_id."""
        if not sucursal or not sucursal.ciudad_id:
            return None
        return self._db.execute(
            select(Ciudad).where(Ciudad.id == sucursal.ciudad_id)
        ).scalar_one_or_none()

    def _wrap_sucursal(self, sucursal: Sucursal) -> _SucursalConCiudad:
        """Envuelve Sucursal con Ciudad para Pydantic."""
        if sucursal is None:
            return None
        ciudad = self._get_ciudad_for_sucursal(sucursal)
        return _SucursalConCiudad(sucursal, ciudad)

    def listar(
        self, usuario: Usuario, search: str | None, ciudad_id: int | None, is_active: bool | None
    ) -> list:
        sucursales = self._repo.listar(empresa_id=usuario.empresa_id, search=search, ciudad_id=ciudad_id, is_active=is_active)
        return [self._wrap_sucursal(s) for s in sucursales]

    def obtener(self, usuario: Usuario, sucursal_id: int):
        sucursal = self._repo.get_by_id_tenant(sucursal_id, usuario.empresa_id)
        if sucursal is None:
            raise SucursalNoEncontradaError
        return self._wrap_sucursal(sucursal)

    def crear(self, usuario: Usuario, datos: SucursalCrear):
        if self._ciudades.get_by_id(datos.ciudad_id) is None:
            raise CiudadNoEncontradaError

        if self._repo.existe_nombre_en_ciudad(datos.nombre, datos.ciudad_id, empresa_id=usuario.empresa_id):
            raise NombreDuplicadoError

        sucursal = Sucursal(
            nombre=datos.nombre,
            ciudad_id=datos.ciudad_id,
            direccion=datos.direccion,
            telefono=datos.telefono,
            is_active=datos.is_active,
        )
        # CU03: Asociar sucursal a empresa del usuario autenticado
        cu03_service = AsociacionesEmpresaService(self._db)
        cu03_service.asignar_empresa_a_sucursal(sucursal, usuario.empresa_id)

        created = self._repo.crear(sucursal)
        return self._wrap_sucursal(created)

    def actualizar(self, usuario: Usuario, sucursal_id: int, datos: SucursalActualizar):
        sucursal = self._repo.get_by_id_tenant(sucursal_id, usuario.empresa_id)
        if sucursal is None:
            raise SucursalNoEncontradaError

        if self._ciudades.get_by_id(datos.ciudad_id) is None:
            raise CiudadNoEncontradaError

        if self._repo.existe_nombre_en_ciudad(
            datos.nombre, datos.ciudad_id, empresa_id=usuario.empresa_id, excluyendo_id=sucursal.id
        ):
            raise NombreDuplicadoError

        sucursal.nombre = datos.nombre
        sucursal.ciudad_id = datos.ciudad_id
        sucursal.direccion = datos.direccion
        sucursal.telefono = datos.telefono
        updated = self._repo.guardar(sucursal)
        return self._wrap_sucursal(updated)

    def cambiar_estado(self, usuario: Usuario, sucursal_id: int, activo: bool):
        sucursal = self._repo.get_by_id_tenant(sucursal_id, usuario.empresa_id)
        if sucursal is None:
            raise SucursalNoEncontradaError
        sucursal.is_active = activo
        updated = self._repo.guardar(sucursal)
        return self._wrap_sucursal(updated)

    def eliminar(self, usuario: Usuario, sucursal_id: int) -> None:
        sucursal = self._repo.get_by_id_tenant(sucursal_id, usuario.empresa_id)
        if sucursal is None:
            raise SucursalNoEncontradaError
        self._repo.eliminar(sucursal)
