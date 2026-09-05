"""Reglas de negocio de CU08 -- Gestionar productos.

El Administrador convierte una propuesta de proveedor (ProductoProveedor) o
registra directamente un producto de FashionStore: completa categoría,
tallas, colores y precio de venta (global, no por sucursal). Las variantes
talla+color se generan/sincronizan automáticamente -- sin stock todavía.
"""

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.image_storage import eliminar_archivo_imagen, guardar_archivo_imagen
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_imagen import ProductoImagen
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.talla import Talla

from .repository import CatalogoLecturaRepository, ProductosRepository, PropuestasProveedorRepository
from .schemas import (
    ColeccionResumen,
    ProductoActualizar,
    ProductoCrear,
    PropuestaProveedorOut,
    ProveedorResumen,
    TemporadaResumen,
)


class ProductoNoEncontradoError(Exception):
    pass


class ProveedorNoEncontradoError(Exception):
    pass


class CategoriaNoEncontradaError(Exception):
    pass


class TemporadaNoEncontradaError(Exception):
    pass


class ColeccionNoEncontradaError(Exception):
    pass


class ColeccionNoPerteneceATemporadaError(Exception):
    """La colección elegida no pertenece a la temporada elegida."""


class TallaInvalidaError(Exception):
    """Alguna talla indicada no existe."""


class ColorInvalidoError(Exception):
    """Algún color indicado no existe."""


class PropuestaNoEncontradaError(Exception):
    pass


class PropuestaNoPerteneceAProveedorError(Exception):
    """La propuesta indicada pertenece a otro proveedor."""


class PropuestaYaConvertidaError(Exception):
    """Esa propuesta ya fue convertida en un producto -- no se duplica."""


class ImagenNoEncontradaError(Exception):
    """La imagen adicional indicada no pertenece a este producto."""


class ProductosService:
    def __init__(self, db: Session):
        self._repo = ProductosRepository(db)
        self._catalogo = CatalogoLecturaRepository(db)
        self._propuestas = PropuestasProveedorRepository(db)

    def listar(
        self,
        search: str | None = None,
        categoria_id: int | None = None,
        temporada_id: int | None = None,
        coleccion_id: int | None = None,
        proveedor_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[Producto]:
        return self._repo.listar(
            search=search,
            categoria_id=categoria_id,
            temporada_id=temporada_id,
            coleccion_id=coleccion_id,
            proveedor_id=proveedor_id,
            is_active=is_active,
        )

    def obtener(self, producto_id: int) -> Producto:
        producto = self._repo.get_by_id(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError
        return producto

    def _validar_referencias(self, datos: ProductoCrear | ProductoActualizar) -> None:
        if self._catalogo.get_proveedor(datos.proveedor_id) is None:
            raise ProveedorNoEncontradoError
        if self._catalogo.get_categoria(datos.categoria_id) is None:
            raise CategoriaNoEncontradaError
        if self._catalogo.get_temporada(datos.temporada_id) is None:
            raise TemporadaNoEncontradaError
        coleccion = self._catalogo.get_coleccion(datos.coleccion_id)
        if coleccion is None:
            raise ColeccionNoEncontradaError
        if coleccion.temporada_id != datos.temporada_id:
            raise ColeccionNoPerteneceATemporadaError

    def _resolver_tallas(self, talla_ids: list[int]) -> list[Talla]:
        tallas = self._catalogo.get_tallas_por_ids(talla_ids)
        if len(tallas) != len(set(talla_ids)):
            raise TallaInvalidaError
        return tallas

    def _resolver_colores(self, color_ids: list[int]) -> list[Color]:
        colores = self._catalogo.get_colores_por_ids(color_ids)
        if len(colores) != len(set(color_ids)):
            raise ColorInvalidoError
        return colores

    def _validar_propuesta(
        self,
        proveedor_id: int,
        producto_proveedor_id: int | None,
        excluyendo_producto_id: int | None = None,
    ) -> None:
        if producto_proveedor_id is None:
            return
        propuesta = self._propuestas.get_by_id(producto_proveedor_id)
        if propuesta is None:
            raise PropuestaNoEncontradaError
        if propuesta.proveedor_id != proveedor_id:
            raise PropuestaNoPerteneceAProveedorError
        if self._repo.existe_producto_proveedor_vinculado(
            producto_proveedor_id, excluyendo_id=excluyendo_producto_id
        ):
            raise PropuestaYaConvertidaError

    def _sincronizar_variantes(
        self, producto: Producto, tallas: list[Talla], colores: list[Color]
    ) -> None:
        deseadas = {(talla.id, color.id) for talla in tallas for color in colores}
        existentes = {(variante.talla_id, variante.color_id): variante for variante in producto.variantes}

        for clave, variante in list(existentes.items()):
            if clave not in deseadas:
                producto.variantes.remove(variante)

        for talla_id, color_id in deseadas:
            if (talla_id, color_id) not in existentes:
                producto.variantes.append(
                    ProductoVariante(talla_id=talla_id, color_id=color_id, is_active=True)
                )

    def crear(self, datos: ProductoCrear) -> Producto:
        self._validar_referencias(datos)
        self._validar_propuesta(datos.proveedor_id, datos.producto_proveedor_id)
        tallas = self._resolver_tallas(datos.talla_ids)
        colores = self._resolver_colores(datos.color_ids)

        producto = Producto(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            proveedor_id=datos.proveedor_id,
            producto_proveedor_id=datos.producto_proveedor_id,
            categoria_id=datos.categoria_id,
            temporada_id=datos.temporada_id,
            coleccion_id=datos.coleccion_id,
            precio_venta=datos.precio_venta,
            is_active=datos.is_active,
            tallas=tallas,
            colores=colores,
        )
        self._sincronizar_variantes(producto, tallas, colores)
        return self._repo.crear(producto)

    def actualizar(self, producto_id: int, datos: ProductoActualizar) -> Producto:
        producto = self.obtener(producto_id)
        self._validar_referencias(datos)
        self._validar_propuesta(
            datos.proveedor_id, datos.producto_proveedor_id, excluyendo_producto_id=producto.id
        )
        tallas = self._resolver_tallas(datos.talla_ids)
        colores = self._resolver_colores(datos.color_ids)

        producto.nombre = datos.nombre
        producto.descripcion = datos.descripcion
        producto.proveedor_id = datos.proveedor_id
        producto.producto_proveedor_id = datos.producto_proveedor_id
        producto.categoria_id = datos.categoria_id
        producto.temporada_id = datos.temporada_id
        producto.coleccion_id = datos.coleccion_id
        producto.precio_venta = datos.precio_venta
        producto.tallas = tallas
        producto.colores = colores

        self._sincronizar_variantes(producto, tallas, colores)
        return self._repo.guardar(producto)

    def cambiar_estado(self, producto_id: int, activo: bool) -> Producto:
        producto = self.obtener(producto_id)
        producto.is_active = activo
        return self._repo.guardar(producto)

    def establecer_imagen_principal(self, producto_id: int, archivo: UploadFile, contenido: bytes) -> Producto:
        producto = self.obtener(producto_id)
        url_anterior = producto.imagen_principal_url
        producto.imagen_principal_url = guardar_archivo_imagen("productos", archivo, contenido)
        producto = self._repo.guardar(producto)
        eliminar_archivo_imagen(url_anterior)
        return producto

    def agregar_imagen(self, producto_id: int, archivo: UploadFile, contenido: bytes) -> Producto:
        producto = self.obtener(producto_id)
        url = guardar_archivo_imagen("productos", archivo, contenido)
        siguiente_orden = len(producto.imagenes)
        producto.imagenes.append(ProductoImagen(url=url, orden=siguiente_orden))
        return self._repo.guardar(producto)

    def eliminar_imagen(self, producto_id: int, imagen_id: int) -> Producto:
        producto = self.obtener(producto_id)
        imagen = next((item for item in producto.imagenes if item.id == imagen_id), None)
        if imagen is None:
            raise ImagenNoEncontradaError
        url = imagen.url
        producto.imagenes.remove(imagen)
        producto = self._repo.guardar(producto)
        eliminar_archivo_imagen(url)
        return producto

    def listar_propuestas(self, proveedor_id: int | None = None) -> list[PropuestaProveedorOut]:
        filas = self._propuestas.listar_disponibles(proveedor_id)
        return [
            PropuestaProveedorOut(
                id=propuesta.id,
                nombre=propuesta.nombre,
                descripcion=propuesta.descripcion,
                disponibilidad=propuesta.disponibilidad,
                proveedor=ProveedorResumen(id=proveedor.id, razon_social=proveedor.razon_social),
                temporada=TemporadaResumen(id=propuesta.temporada.id, nombre=propuesta.temporada.nombre),
                coleccion=ColeccionResumen(id=propuesta.coleccion.id, nombre=propuesta.coleccion.nombre),
            )
            for propuesta, proveedor in filas
        ]
