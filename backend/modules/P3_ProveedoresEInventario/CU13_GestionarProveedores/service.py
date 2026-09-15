"""Reglas de negocio de Gestión de Proveedores."""

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.image_storage import eliminar_archivo_imagen, guardar_archivo_imagen
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_proveedor import (
    EstadoProductoProveedor,
    ProductoProveedor,
)
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor

from .repository import ProductosProveedorRepository, ProveedoresRepository
from .schemas import (
    ProductoProveedorActualizar,
    ProductoProveedorCrear,
    ProductoProveedorOut,
    ProveedorActualizar,
    ProveedorCrear,
    VariantesPorColorOut,
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


class ProductoNoEncontradoError(Exception):
    """No existe, o no pertenece al proveedor autenticado (mismo mensaje: no se
    revela la existencia de productos de otros proveedores)."""


class ProductoRechazadoError(Exception):
    """La propuesta fue rechazada por el Administrador; el proveedor ya no
    puede modificarla (ni sus datos, ni su disponibilidad, ni su imagen)."""


class PanelProveedorService:
    """Toda operación recibe proveedor_id ya resuelto desde el usuario
    autenticado (nunca desde un id que el cliente pueda manipular) — así se
    garantiza que un PROVEEDOR solo vea/edite lo suyo.

    El proveedor propone nombre/descripción/imagen/disponibilidad. Categoría,
    temporada, colección, precio, tallas y colores los decide el
    Administrador al convertir la propuesta en un Producto real (CU08) — esta
    clase nunca los pide ni los valida."""

    def __init__(self, db: Session):
        self._proveedores = ProveedoresRepository(db)
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

    def _obtener_orm(self, proveedor_id: int, producto_id: int) -> ProductoProveedor:
        producto = self._productos.get_by_id(producto_id)
        if producto is None or producto.proveedor_id != proveedor_id:
            raise ProductoNoEncontradoError
        return producto

    def _obtener_orm_editable(self, proveedor_id: int, producto_id: int) -> ProductoProveedor:
        """Igual que _obtener_orm, pero además rechaza la operación si el
        Administrador ya rechazó esta propuesta -- el proveedor no puede
        modificarla de una forma que genere inconsistencias con esa decisión."""
        producto = self._obtener_orm(proveedor_id, producto_id)
        if producto.estado == EstadoProductoProveedor.RECHAZADO:
            raise ProductoRechazadoError
        return producto

    @staticmethod
    def _agrupar_variantes_por_color(producto_real: Producto) -> list[VariantesPorColorOut]:
        por_color: dict[str, list[str]] = {}
        for variante in producto_real.variantes:
            if not variante.is_active:
                continue
            por_color.setdefault(variante.color.nombre, []).append(variante.talla.nombre)
        return [
            VariantesPorColorOut(color=color, tallas=tallas) for color, tallas in por_color.items()
        ]

    def _a_salida(self, producto: ProductoProveedor) -> ProductoProveedorOut:
        producto_real = (
            self._productos.get_producto_vinculado(producto.id)
            if producto.estado == EstadoProductoProveedor.APROBADO
            else None
        )
        variantes = self._agrupar_variantes_por_color(producto_real) if producto_real else []
        return ProductoProveedorOut(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            imagen_url=producto.imagen_url,
            disponibilidad=producto.disponibilidad,
            is_active=producto.is_active,
            estado=producto.estado.value,
            variantes=variantes,
        )

    def listar_mis_productos(self, proveedor_id: int) -> list[ProductoProveedorOut]:
        return [self._a_salida(p) for p in self._productos.listar_por_proveedor(proveedor_id)]

    def obtener_mi_producto(self, proveedor_id: int, producto_id: int) -> ProductoProveedorOut:
        return self._a_salida(self._obtener_orm(proveedor_id, producto_id))

    def crear_producto(
        self, proveedor_id: int, datos: ProductoProveedorCrear
    ) -> ProductoProveedorOut:
        producto = ProductoProveedor(
            proveedor_id=proveedor_id,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            disponibilidad=datos.disponibilidad,
            is_active=True,
        )
        return self._a_salida(self._productos.crear(producto))

    def actualizar_producto(
        self, proveedor_id: int, producto_id: int, datos: ProductoProveedorActualizar
    ) -> ProductoProveedorOut:
        producto = self._obtener_orm_editable(proveedor_id, producto_id)
        producto.nombre = datos.nombre
        producto.descripcion = datos.descripcion
        return self._a_salida(self._productos.guardar(producto))

    def cambiar_disponibilidad(
        self, proveedor_id: int, producto_id: int, disponible: bool
    ) -> ProductoProveedorOut:
        producto = self._obtener_orm_editable(proveedor_id, producto_id)
        producto.disponibilidad = disponible
        return self._a_salida(self._productos.guardar(producto))

    def cambiar_estado_producto(
        self, proveedor_id: int, producto_id: int, activo: bool
    ) -> ProductoProveedorOut:
        producto = self._obtener_orm(proveedor_id, producto_id)
        producto.is_active = activo
        return self._a_salida(self._productos.guardar(producto))

    def establecer_imagen(
        self, proveedor_id: int, producto_id: int, archivo: UploadFile, contenido: bytes
    ) -> ProductoProveedorOut:
        producto = self._obtener_orm_editable(proveedor_id, producto_id)
        url_anterior = producto.imagen_url
        producto.imagen_url = guardar_archivo_imagen("productos-proveedor", archivo, contenido)
        producto = self._productos.guardar(producto)
        eliminar_archivo_imagen(url_anterior)
        return self._a_salida(producto)
