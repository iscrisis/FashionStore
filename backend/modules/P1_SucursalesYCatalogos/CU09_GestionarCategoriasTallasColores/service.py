"""Reglas de negocio de CU09 — Gestionar categorías, tallas y colores."""

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.image_storage import eliminar_archivo_imagen, guardar_archivo_imagen
from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.talla import Talla

from .repository import CategoriasRepository, ColoresRepository, TallasRepository
from .schemas import ItemCatalogoActualizar, ItemCatalogoCrear


class RegistroNoEncontradoError(Exception):
    pass


class NombreDuplicadoError(Exception):
    """Ya existe un registro con ese nombre en el mismo catálogo."""


class CategoriasService:
    def __init__(self, db: Session):
        self._repo = CategoriasRepository(db)

    def listar(self, search: str | None, is_active: bool | None) -> list[Categoria]:
        return self._repo.listar(search=search, is_active=is_active)

    def obtener(self, categoria_id: int) -> Categoria:
        categoria = self._repo.get_by_id(categoria_id)
        if categoria is None:
            raise RegistroNoEncontradoError
        return categoria

    def crear(self, datos: ItemCatalogoCrear) -> Categoria:
        if self._repo.existe_nombre(datos.nombre):
            raise NombreDuplicadoError
        return self._repo.crear(Categoria(nombre=datos.nombre, is_active=datos.is_active))

    def actualizar(self, categoria_id: int, datos: ItemCatalogoActualizar) -> Categoria:
        categoria = self.obtener(categoria_id)
        if self._repo.existe_nombre(datos.nombre, excluyendo_id=categoria.id):
            raise NombreDuplicadoError
        categoria.nombre = datos.nombre
        return self._repo.guardar(categoria)

    def cambiar_estado(self, categoria_id: int, activo: bool) -> Categoria:
        categoria = self.obtener(categoria_id)
        categoria.is_active = activo
        return self._repo.guardar(categoria)

    def establecer_imagen(self, categoria_id: int, archivo: UploadFile, contenido: bytes) -> Categoria:
        categoria = self.obtener(categoria_id)
        url_anterior = categoria.imagen_url
        categoria.imagen_url = guardar_archivo_imagen("categorias", archivo, contenido)
        categoria = self._repo.guardar(categoria)
        eliminar_archivo_imagen(url_anterior)
        return categoria

    def eliminar_imagen(self, categoria_id: int) -> Categoria:
        categoria = self.obtener(categoria_id)
        url_anterior = categoria.imagen_url
        categoria.imagen_url = None
        categoria = self._repo.guardar(categoria)
        eliminar_archivo_imagen(url_anterior)
        return categoria


class TallasService:
    def __init__(self, db: Session):
        self._repo = TallasRepository(db)

    def listar(self, search: str | None, is_active: bool | None) -> list[Talla]:
        return self._repo.listar(search=search, is_active=is_active)

    def obtener(self, talla_id: int) -> Talla:
        talla = self._repo.get_by_id(talla_id)
        if talla is None:
            raise RegistroNoEncontradoError
        return talla

    def crear(self, datos: ItemCatalogoCrear) -> Talla:
        if self._repo.existe_nombre(datos.nombre):
            raise NombreDuplicadoError
        return self._repo.crear(Talla(nombre=datos.nombre, is_active=datos.is_active))

    def actualizar(self, talla_id: int, datos: ItemCatalogoActualizar) -> Talla:
        talla = self.obtener(talla_id)
        if self._repo.existe_nombre(datos.nombre, excluyendo_id=talla.id):
            raise NombreDuplicadoError
        talla.nombre = datos.nombre
        return self._repo.guardar(talla)

    def cambiar_estado(self, talla_id: int, activo: bool) -> Talla:
        talla = self.obtener(talla_id)
        talla.is_active = activo
        return self._repo.guardar(talla)


class ColoresService:
    def __init__(self, db: Session):
        self._repo = ColoresRepository(db)

    def listar(self, search: str | None, is_active: bool | None) -> list[Color]:
        return self._repo.listar(search=search, is_active=is_active)

    def obtener(self, color_id: int) -> Color:
        color = self._repo.get_by_id(color_id)
        if color is None:
            raise RegistroNoEncontradoError
        return color

    def crear(self, datos: ItemCatalogoCrear) -> Color:
        if self._repo.existe_nombre(datos.nombre):
            raise NombreDuplicadoError
        return self._repo.crear(Color(nombre=datos.nombre, is_active=datos.is_active))

    def actualizar(self, color_id: int, datos: ItemCatalogoActualizar) -> Color:
        color = self.obtener(color_id)
        if self._repo.existe_nombre(datos.nombre, excluyendo_id=color.id):
            raise NombreDuplicadoError
        color.nombre = datos.nombre
        return self._repo.guardar(color)

    def cambiar_estado(self, color_id: int, activo: bool) -> Color:
        color = self.obtener(color_id)
        color.is_active = activo
        return self._repo.guardar(color)
