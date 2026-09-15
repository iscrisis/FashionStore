"""Reglas de negocio de CU15 -- Registrar recepción de mercadería (Panel del Encargado).

sucursal_id y usuario_id llegan SIEMPRE ya resueltos desde el usuario
autenticado (ver _sucursal_id_del_actor en router.py, mismo patrón que
CU14) -- nunca desde un id que el cliente pueda manipular. Toda la
validación (proveedor, producto, variante, cantidades) ocurre en backend:
Angular es solo la vista, no la autoridad.

registrar() hace TODO en una sola transacción: valida cada detalle antes de
escribir nada, luego crea la recepción + sus detalles + suma StockSucursal, y
recién al final hace un único commit. Si algo falla antes de ese commit, la
sesión no confirma ningún cambio (ver get_db en app/db/session.py: sin
autocommit) -- no puede quedar una recepción a medias.
"""

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.detalle_recepcion_mercaderia import (
    DetalleRecepcionMercaderia,
)
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.recepcion_mercaderia import RecepcionMercaderia
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .repository import (
    ProductoLecturaRepository,
    ProveedorLecturaRepository,
    RecepcionMercaderiaRepository,
    StockSucursalIncrementoRepository,
)
from .schemas import (
    CategoriaResumen,
    ColeccionResumen,
    DetalleRecepcionOut,
    ProductoParaRecepcionOut,
    ProductoResumen,
    ProveedorResumen,
    RecepcionOut,
    RegistrarRecepcionRequest,
    SucursalResumen,
    UsuarioResumen,
    VarianteParaRecepcionOut,
)


class ProveedorNoEncontradoError(Exception):
    pass


class ProveedorInactivoError(Exception):
    pass


class ProductoNoEncontradoError(Exception):
    """No existe, está inactivo, o no pertenece al proveedor indicado."""


class VarianteNoEncontradaError(Exception):
    """No existe, está inactiva, o no pertenece al producto indicado."""


class VarianteDuplicadaError(Exception):
    """La misma variante aparece más de una vez en la misma recepción."""


class RecepcionMercaderiaService:
    def __init__(self, db: Session):
        self._db = db
        self._proveedores = ProveedorLecturaRepository(db)
        self._productos = ProductoLecturaRepository(db)
        self._recepciones = RecepcionMercaderiaRepository(db)
        self._stock = StockSucursalIncrementoRepository(db)

    def listar_proveedores_disponibles(self) -> list[Proveedor]:
        return self._proveedores.listar_activos()

    def listar_productos_del_proveedor(self, proveedor_id: int) -> list[ProductoParaRecepcionOut]:
        proveedor = self._proveedores.get_by_id(proveedor_id)
        if proveedor is None:
            raise ProveedorNoEncontradoError

        resultado: list[ProductoParaRecepcionOut] = []
        for producto in self._productos.listar_por_proveedor(proveedor_id):
            variantes_activas = [v for v in producto.variantes if v.is_active]
            if not variantes_activas:
                continue
            resultado.append(
                ProductoParaRecepcionOut(
                    id=producto.id,
                    nombre=producto.nombre,
                    imagen_principal_url=producto.imagen_principal_url,
                    categoria=CategoriaResumen.model_validate(producto.categoria),
                    coleccion=ColeccionResumen.model_validate(producto.coleccion),
                    variantes=[
                        VarianteParaRecepcionOut.model_validate(variante)
                        for variante in variantes_activas
                    ],
                )
            )
        return resultado

    def _validar_detalle(
        self, proveedor_id: int, detalle
    ) -> tuple[Producto, ProductoVariante]:
        producto = self._productos.get_by_id(detalle.producto_id)
        if producto is None or not producto.is_active or producto.proveedor_id != proveedor_id:
            raise ProductoNoEncontradoError

        variante = self._productos.get_variante_by_id(detalle.producto_variante_id)
        if variante is None or not variante.is_active or variante.producto_id != producto.id:
            raise VarianteNoEncontradaError

        return producto, variante

    def registrar(
        self, sucursal_id: int, actor: Usuario, datos: RegistrarRecepcionRequest
    ) -> RecepcionOut:
        proveedor = self._proveedores.get_by_id(datos.proveedor_id)
        if proveedor is None:
            raise ProveedorNoEncontradoError
        if not proveedor.is_active:
            raise ProveedorInactivoError

        variantes_vistas: set[int] = set()
        validados: list[tuple[Producto, ProductoVariante]] = []
        for detalle in datos.detalles:
            if detalle.producto_variante_id in variantes_vistas:
                raise VarianteDuplicadaError
            variantes_vistas.add(detalle.producto_variante_id)
            validados.append(self._validar_detalle(proveedor.id, detalle))

        recepcion = RecepcionMercaderia(
            proveedor_id=proveedor.id,
            sucursal_id=sucursal_id,
            usuario_id=actor.id,
            observacion=datos.observacion,
        )
        self._recepciones.crear(recepcion)

        detalles_out: list[DetalleRecepcionOut] = []
        for detalle_in, (producto, variante) in zip(datos.detalles, validados):
            fila = DetalleRecepcionMercaderia(
                recepcion_id=recepcion.id,
                producto_variante_id=variante.id,
                cantidad_recibida=detalle_in.cantidad_recibida,
            )
            self._recepciones.agregar_detalle(fila)

            stock = self._stock.incrementar(sucursal_id, variante.id, detalle_in.cantidad_recibida)

            detalles_out.append(
                DetalleRecepcionOut(
                    producto=ProductoResumen(
                        id=producto.id,
                        nombre=producto.nombre,
                        imagen_principal_url=producto.imagen_principal_url,
                    ),
                    variante=VarianteParaRecepcionOut.model_validate(variante),
                    cantidad_recibida=detalle_in.cantidad_recibida,
                    stock_resultante=stock.cantidad,
                )
            )

        self._recepciones.confirmar()
        self._db.refresh(recepcion)

        return RecepcionOut(
            id=recepcion.id,
            proveedor=ProveedorResumen.model_validate(proveedor),
            sucursal=SucursalResumen.model_validate(recepcion.sucursal),
            registrado_por=UsuarioResumen(id=actor.id, nombre=actor.nombre),
            fecha_hora=recepcion.fecha_hora,
            observacion=recepcion.observacion,
            detalles=detalles_out,
        )
