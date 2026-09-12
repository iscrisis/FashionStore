"""Reglas de negocio de Gestión de Proveedores."""

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.producto_proveedor import ProductoProveedor
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada

from .repository import (
    CatalogoLecturaRepository,
    ProductosProveedorRepository,
    ProveedoresRepository,
)
from .schemas import (
    ProductoProveedorActualizar,
    ProductoProveedorCrear,
    ProveedorActualizar,
    ProveedorCrear,
)


class ProveedorNoEncontradoError(Exception):
    pass


class RazonSocialDuplicadaError(Exception):
    """Ya existe un proveedor con esa razón social."""


class ProveedoresService:
    def __init__(self, db: Session):
        self._repo = ProveedoresRepository(db)

    def listar(self, search: str | None, is_active: bool | None) -> list[Proveedor]:
        return self._repo.listar(search=search, is_active=is_active)

    def obtener(self, proveedor_id: int) -> Proveedor:
        proveedor = self._repo.get_by_id(proveedor_id)
        if proveedor is None:
            raise ProveedorNoEncontradoError
        return proveedor

    def crear(self, datos: ProveedorCrear) -> Proveedor:
        if self._repo.existe_razon_social(datos.razon_social):
            raise RazonSocialDuplicadaError

        proveedor = Proveedor(
            razon_social=datos.razon_social,
            nombre_contacto=datos.nombre_contacto,
            correo=datos.correo,
            telefono=datos.telefono,
            is_active=datos.is_active,
        )
        return self._repo.crear(proveedor)

    def actualizar(self, proveedor_id: int, datos: ProveedorActualizar) -> Proveedor:
        proveedor = self.obtener(proveedor_id)

        if self._repo.existe_razon_social(datos.razon_social, excluyendo_id=proveedor.id):
            raise RazonSocialDuplicadaError

        proveedor.razon_social = datos.razon_social
        proveedor.nombre_contacto = datos.nombre_contacto
        proveedor.correo = datos.correo
        proveedor.telefono = datos.telefono
        return self._repo.guardar(proveedor)

    def cambiar_estado(self, proveedor_id: int, activo: bool) -> Proveedor:
        proveedor = self.obtener(proveedor_id)
        proveedor.is_active = activo
        return self._repo.guardar(proveedor)


class TemporadaNoEncontradaError(Exception):
    pass


class ColeccionNoEncontradaError(Exception):
    pass


class ColeccionNoPerteneceATemporadaError(Exception):
    """La colección elegida no pertenece a la temporada elegida."""


class ProductoNoEncontradoError(Exception):
    """No existe, o no pertenece al proveedor autenticado (mismo mensaje: no se
    revela la existencia de productos de otros proveedores)."""


class PanelProveedorService:
    """Toda operación recibe proveedor_id ya resuelto desde el usuario
    autenticado (nunca desde un id que el cliente pueda manipular) — así se
    garantiza que un PROVEEDOR solo vea/edite lo suyo."""

    def __init__(self, db: Session):
        self._proveedores = ProveedoresRepository(db)
        self._catalogo = CatalogoLecturaRepository(db)
        self._productos = ProductosProveedorRepository(db)

    def mi_perfil(self, proveedor_id: int) -> Proveedor:
        proveedor = self._proveedores.get_by_id(proveedor_id)
        if proveedor is None:
            raise ProveedorNoEncontradoError
        return proveedor

    def actualizar_mi_perfil(self, proveedor_id: int, datos: ProveedorActualizar) -> Proveedor:
        proveedor = self.mi_perfil(proveedor_id)
        if self._proveedores.existe_razon_social(datos.razon_social, excluyendo_id=proveedor.id):
            raise RazonSocialDuplicadaError
        proveedor.razon_social = datos.razon_social
        proveedor.nombre_contacto = datos.nombre_contacto
        proveedor.correo = datos.correo
        proveedor.telefono = datos.telefono
        return self._proveedores.guardar(proveedor)

    def temporadas_disponibles(self) -> list[Temporada]:
        return self._catalogo.listar_temporadas_activas()

    def colecciones_disponibles(self, temporada_id: int) -> list[Coleccion]:
        return self._catalogo.listar_colecciones_activas(temporada_id)

    def listar_mis_productos(self, proveedor_id: int) -> list[ProductoProveedor]:
        return self._productos.listar_por_proveedor(proveedor_id)

    def obtener_mi_producto(self, proveedor_id: int, producto_id: int) -> ProductoProveedor:
        producto = self._productos.get_by_id(producto_id)
        if producto is None or producto.proveedor_id != proveedor_id:
            raise ProductoNoEncontradoError
        return producto

    def _validar_temporada_y_coleccion(self, temporada_id: int, coleccion_id: int) -> None:
        if self._catalogo.get_temporada(temporada_id) is None:
            raise TemporadaNoEncontradaError
        coleccion = self._catalogo.get_coleccion(coleccion_id)
        if coleccion is None:
            raise ColeccionNoEncontradaError
        if coleccion.temporada_id != temporada_id:
            raise ColeccionNoPerteneceATemporadaError

    def crear_producto(
        self, proveedor_id: int, datos: ProductoProveedorCrear
    ) -> ProductoProveedor:
        self._validar_temporada_y_coleccion(datos.temporada_id, datos.coleccion_id)
        producto = ProductoProveedor(
            proveedor_id=proveedor_id,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            temporada_id=datos.temporada_id,
            coleccion_id=datos.coleccion_id,
            disponibilidad=datos.disponibilidad,
            is_active=True,
        )
        return self._productos.crear(producto)

    def actualizar_producto(
        self, proveedor_id: int, producto_id: int, datos: ProductoProveedorActualizar
    ) -> ProductoProveedor:
        producto = self.obtener_mi_producto(proveedor_id, producto_id)
        self._validar_temporada_y_coleccion(datos.temporada_id, datos.coleccion_id)
        producto.nombre = datos.nombre
        producto.descripcion = datos.descripcion
        producto.temporada_id = datos.temporada_id
        producto.coleccion_id = datos.coleccion_id
        return self._productos.guardar(producto)

    def cambiar_disponibilidad(
        self, proveedor_id: int, producto_id: int, disponible: bool
    ) -> ProductoProveedor:
        producto = self.obtener_mi_producto(proveedor_id, producto_id)
        producto.disponibilidad = disponible
        return self._productos.guardar(producto)

    def cambiar_estado_producto(
        self, proveedor_id: int, producto_id: int, activo: bool
    ) -> ProductoProveedor:
        producto = self.obtener_mi_producto(proveedor_id, producto_id)
        producto.is_active = activo
        return self._productos.guardar(producto)
