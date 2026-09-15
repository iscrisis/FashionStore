"""Reglas de negocio de CU16 -- Registrar movimientos de inventario (Panel del Encargado).

sucursal_id y usuario_id llegan SIEMPRE ya resueltos desde el usuario
autenticado (ver _sucursal_id_del_actor en router.py, mismo patrón que CU14 y
CU15) -- nunca desde un id que el cliente pueda manipular. Toda la validación
(variante, cantidad, stock suficiente) ocurre en backend: Angular es solo la
vista, no la autoridad.

registrar() hace TODO en una sola transacción: valida la variante y calcula
stock_resultante antes de escribir nada, luego crea el movimiento + ajusta
StockSucursal, y recién al final hace un único commit (ver
MovimientoInventarioRepository.confirmar). Si algo falla antes de ese commit,
la sesión no confirma ningún cambio (ver get_db en app/db/session.py: sin
autocommit) -- no puede quedar un movimiento sin su ajuste de stock, ni
viceversa.

Es un CU independiente de CU15 (recepción de proveedor): no reutiliza su
tabla ni su lógica de suma -- aquí el delta puede ser positivo o negativo, y
un ajuste negativo que dejaría el stock por debajo de 0 se rechaza.
"""

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.movimiento_inventario import (
    MovimientoInventario,
    TipoMovimientoInventario,
)
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

from .repository import MovimientoInventarioRepository, ProductoLecturaRepository, StockAjusteRepository
from .schemas import (
    ColorResumen,
    MovimientoOut,
    ProductoConVariantesOut,
    ProductoResumen,
    RegistrarMovimientoRequest,
    TallaResumen,
    UsuarioResumen,
    VarianteConStockOut,
    VarianteResumen,
)


class VarianteNoEncontradaError(Exception):
    """No existe, está inactiva, o su producto está inactivo."""


class StockInsuficienteError(Exception):
    """El ajuste negativo dejaría el stock de la variante por debajo de 0."""


class MovimientosInventarioService:
    def __init__(self, db: Session):
        self._db = db
        self._productos = ProductoLecturaRepository(db)
        self._stock = StockAjusteRepository(db)
        self._movimientos = MovimientoInventarioRepository(db)

    def listar_productos(self, sucursal_id: int, search: str | None) -> list[ProductoConVariantesOut]:
        productos = self._productos.listar_activos(search)
        stock_por_variante = self._stock.listar_por_sucursal(sucursal_id)

        resultado: list[ProductoConVariantesOut] = []
        for producto in productos:
            variantes_activas = [v for v in producto.variantes if v.is_active]
            if not variantes_activas:
                continue
            resultado.append(
                ProductoConVariantesOut(
                    id=producto.id,
                    nombre=producto.nombre,
                    imagen_principal_url=producto.imagen_principal_url,
                    variantes=[
                        VarianteConStockOut(
                            id=variante.id,
                            talla=TallaResumen.model_validate(variante.talla),
                            color=ColorResumen.model_validate(variante.color),
                            cantidad=stock_por_variante.get(variante.id, 0),
                        )
                        for variante in variantes_activas
                    ],
                )
            )
        return resultado

    def _resolver_variante(self, variante_id: int) -> tuple[Producto, ProductoVariante]:
        variante = self._productos.get_variante_by_id(variante_id)
        if variante is None or not variante.is_active:
            raise VarianteNoEncontradaError
        producto = self._productos.get_by_id(variante.producto_id)
        if producto is None or not producto.is_active:
            raise VarianteNoEncontradaError
        return producto, variante

    def _a_salida(
        self, movimiento: MovimientoInventario, producto: Producto, variante: ProductoVariante, actor_nombre: str
    ) -> MovimientoOut:
        return MovimientoOut(
            id=movimiento.id,
            producto=ProductoResumen(
                id=producto.id, nombre=producto.nombre, imagen_principal_url=producto.imagen_principal_url
            ),
            variante=VarianteResumen.model_validate(variante),
            tipo=movimiento.tipo.value,
            cantidad=movimiento.cantidad,
            motivo=movimiento.motivo,
            stock_anterior=movimiento.stock_anterior,
            stock_resultante=movimiento.stock_resultante,
            fecha_hora=movimiento.fecha_hora,
            registrado_por=UsuarioResumen(id=movimiento.usuario_id, nombre=actor_nombre),
        )

    def registrar(
        self, sucursal_id: int, actor: Usuario, datos: RegistrarMovimientoRequest
    ) -> MovimientoOut:
        producto, variante = self._resolver_variante(datos.producto_variante_id)

        stock_actual_row = self._stock.get_by_sucursal_y_variante(sucursal_id, variante.id)
        stock_actual = stock_actual_row.cantidad if stock_actual_row is not None else 0

        tipo = TipoMovimientoInventario(datos.tipo)
        if tipo == TipoMovimientoInventario.AJUSTE_POSITIVO:
            stock_resultante = stock_actual + datos.cantidad
        else:
            stock_resultante = stock_actual - datos.cantidad
            if stock_resultante < 0:
                raise StockInsuficienteError

        movimiento = MovimientoInventario(
            sucursal_id=sucursal_id,
            producto_variante_id=variante.id,
            usuario_id=actor.id,
            tipo=tipo,
            cantidad=datos.cantidad,
            motivo=datos.motivo,
            stock_anterior=stock_actual,
            stock_resultante=stock_resultante,
        )
        self._movimientos.crear(movimiento)
        self._stock.fijar_resultado(sucursal_id, variante.id, stock_resultante)
        self._movimientos.confirmar()
        self._db.refresh(movimiento)

        return self._a_salida(movimiento, producto, variante, actor.nombre)

    def listar_historial(self, sucursal_id: int, limit: int) -> list[MovimientoOut]:
        filas = self._movimientos.listar_por_sucursal(sucursal_id, limit)

        productos_cache: dict[int, Producto | None] = {}
        usuarios_cache: dict[int, str] = {}
        resultado: list[MovimientoOut] = []

        for movimiento in filas:
            variante = movimiento.producto_variante
            producto_id = variante.producto_id
            if producto_id not in productos_cache:
                productos_cache[producto_id] = self._productos.get_by_id(producto_id)
            producto = productos_cache[producto_id]
            if producto is None:
                continue

            if movimiento.usuario_id not in usuarios_cache:
                usuario = self._movimientos.get_usuario_by_id(movimiento.usuario_id)
                usuarios_cache[movimiento.usuario_id] = usuario.nombre if usuario else "Usuario eliminado"

            resultado.append(
                self._a_salida(movimiento, producto, variante, usuarios_cache[movimiento.usuario_id])
            )

        return resultado
