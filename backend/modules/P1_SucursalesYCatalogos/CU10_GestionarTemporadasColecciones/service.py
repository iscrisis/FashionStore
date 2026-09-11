"""Reglas de negocio de CU10 — Gestionar temporadas y colecciones."""

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.image_storage import eliminar_archivo_imagen, guardar_archivo_imagen
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada

from .repository import ColeccionesRepository, TemporadasRepository
from .schemas import ColeccionActualizar, ColeccionCrear, TemporadaActualizar, TemporadaCrear


class RegistroNoEncontradoError(Exception):
    pass


class TemporadaNoEncontradaError(Exception):
    """La temporada indicada no existe (validación de "temporada existente")."""


class NombreDuplicadoError(Exception):
    """Ya existe un registro con ese nombre (temporada global, o colección en la misma temporada)."""


class TemporadasService:
    def __init__(self, db: Session):
        self._repo = TemporadasRepository(db)

    def listar(self, search: str | None, is_active: bool | None) -> list[Temporada]:
        return self._repo.listar(search=search, is_active=is_active)

    def obtener(self, temporada_id: int) -> Temporada:
        temporada = self._repo.get_by_id(temporada_id)
        if temporada is None:
            raise RegistroNoEncontradoError
        return temporada

    def crear(self, datos: TemporadaCrear) -> Temporada:
        if self._repo.existe_nombre(datos.nombre):
            raise NombreDuplicadoError
        return self._repo.crear(
            Temporada(
                nombre=datos.nombre,
                fecha_inicio=datos.fecha_inicio,
                fecha_fin=datos.fecha_fin,
                is_active=datos.is_active,
            )
        )

    def actualizar(self, temporada_id: int, datos: TemporadaActualizar) -> Temporada:
        temporada = self.obtener(temporada_id)
        if self._repo.existe_nombre(datos.nombre, excluyendo_id=temporada.id):
            raise NombreDuplicadoError
        temporada.nombre = datos.nombre
        temporada.fecha_inicio = datos.fecha_inicio
        temporada.fecha_fin = datos.fecha_fin
        return self._repo.guardar(temporada)

    def cambiar_estado(self, temporada_id: int, activo: bool) -> Temporada:
        temporada = self.obtener(temporada_id)
        temporada.is_active = activo
        return self._repo.guardar(temporada)


class ColeccionesService:
    def __init__(self, db: Session):
        self._repo = ColeccionesRepository(db)
        self._temporadas = TemporadasRepository(db)

    def listar(
        self, search: str | None, temporada_id: int | None, is_active: bool | None
    ) -> list[Coleccion]:
        return self._repo.listar(search=search, temporada_id=temporada_id, is_active=is_active)

    def obtener(self, coleccion_id: int) -> Coleccion:
        coleccion = self._repo.get_by_id(coleccion_id)
        if coleccion is None:
            raise RegistroNoEncontradoError
        return coleccion

    def crear(self, datos: ColeccionCrear) -> Coleccion:
        if self._temporadas.get_by_id(datos.temporada_id) is None:
            raise TemporadaNoEncontradaError

        if self._repo.existe_nombre_en_temporada(datos.nombre, datos.temporada_id):
            raise NombreDuplicadoError

        coleccion = Coleccion(
            nombre=datos.nombre,
            temporada_id=datos.temporada_id,
            descripcion=datos.descripcion,
            is_active=datos.is_active,
        )
        return self._repo.crear(coleccion)

    def actualizar(self, coleccion_id: int, datos: ColeccionActualizar) -> Coleccion:
        coleccion = self.obtener(coleccion_id)

        if self._temporadas.get_by_id(datos.temporada_id) is None:
            raise TemporadaNoEncontradaError

        if self._repo.existe_nombre_en_temporada(
            datos.nombre, datos.temporada_id, excluyendo_id=coleccion.id
        ):
            raise NombreDuplicadoError

        coleccion.nombre = datos.nombre
        coleccion.temporada_id = datos.temporada_id
        coleccion.descripcion = datos.descripcion
        return self._repo.guardar(coleccion)

    def cambiar_estado(self, coleccion_id: int, activo: bool) -> Coleccion:
        coleccion = self.obtener(coleccion_id)
        coleccion.is_active = activo
        return self._repo.guardar(coleccion)

    def establecer_destacada_inicio(self, coleccion_id: int, destacada: bool) -> Coleccion:
        coleccion = self.obtener(coleccion_id)
        if destacada:
            self._repo.desmarcar_destacadas(excluyendo_id=coleccion_id)
        coleccion.es_destacada_inicio = destacada
        return self._repo.guardar(coleccion)

    def establecer_imagen_destacada(
        self, coleccion_id: int, archivo: UploadFile, contenido: bytes
    ) -> Coleccion:
        coleccion = self.obtener(coleccion_id)
        url_anterior = coleccion.imagen_destacada_url
        coleccion.imagen_destacada_url = guardar_archivo_imagen("colecciones", archivo, contenido)
        coleccion = self._repo.guardar(coleccion)
        eliminar_archivo_imagen(url_anterior)
        return coleccion

    def obtener_destacada_publica(self) -> Coleccion | None:
        return self._repo.obtener_destacada_activa()
