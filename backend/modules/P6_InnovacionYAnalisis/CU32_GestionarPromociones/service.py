"""Reglas de negocio de CU32 -- Gestionar promociones (Administrador).

`estado` es SIEMPRE derivado, nunca guardado (ver Models/promocion.py):
  - `activa == False` -> DESACTIVADA (el Administrador la apagó a mano; gana
    sobre cualquier fecha).
  - hoy < fecha_inicio -> PROGRAMADA.
  - fecha_inicio <= hoy <= fecha_fin -> ACTIVA.
  - hoy > fecha_fin -> FINALIZADA.
No hace falta cron: cada GET vuelve a calcularlo contra la fecha actual.

crear()/editar() validan, en este orden, ANTES de tocar la base:
  1. fecha_fin >= fecha_inicio (el porcentaje y "al menos un producto" ya
     los valida Pydantic -- Field(gt=0, lt=100) / min_length=1, ver
     schemas.py).
  2. Todos los `producto_ids` existen y están activos.
  3. Ninguno de esos productos ya tiene otra promoción `activa` cuyo rango
     se cruce con el nuevo (ver PromocionRepository.existe_solapamiento) --
     nunca se acumulan descuentos.
editar() además rechaza una promoción FINALIZADA o DESACTIVADA -- ya cumplió
su ciclo, no tiene sentido reabrirla para editarla (sí se puede seguir
consultando con VER).

desactivar() SOLO apaga la bandera `activa` -- nunca hay un DELETE físico en
este módulo (ver Models/promocion.py): una promoción que ya tuvo vigencia
queda para siempre en el historial, aunque dejó de aplicar.

Esta clase NUNCA modifica `Producto.precio_venta` ni ninguna fila de
StockSucursal -- una promoción solo afecta el PRECIO EFECTIVO (ver
precio_efectivo.py), nunca reserva ni descuenta stock, ni genera ningún
movimiento de inventario.
"""

from datetime import date

from decimal import Decimal

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P6_InnovacionYAnalisis.Models.promocion import EstadoPromocion, Promocion

from .repository import ProductoLecturaRepository, PromocionRepository
from .schemas import (
    CrearPromocionRequest,
    EditarPromocionRequest,
    ProductoPromocionOut,
    PromocionDetalleOut,
    PromocionListadoOut,
)

_ESTADOS_NO_EDITABLES = (EstadoPromocion.FINALIZADA, EstadoPromocion.DESACTIVADA)


class RangoFechaInvalidoError(Exception):
    """`fecha_fin` es anterior a `fecha_inicio`."""


class ProductoNoEncontradoError(Exception):
    """Alguno de los `producto_ids` no existe, o no está activo."""


class SolapamientoError(Exception):
    """Al menos uno de los productos ya tiene otra promoción activa cuyo
    rango de fechas se cruza con el nuevo."""


class PromocionNoEncontradaError(Exception):
    pass


class PromocionNoEditableError(Exception):
    """La promoción ya está FINALIZADA o DESACTIVADA -- no se puede editar,
    solo consultar (VER)."""


def _calcular_estado(promocion: Promocion, hoy: date) -> EstadoPromocion:
    if not promocion.activa:
        return EstadoPromocion.DESACTIVADA
    if hoy < promocion.fecha_inicio:
        return EstadoPromocion.PROGRAMADA
    if hoy <= promocion.fecha_fin:
        return EstadoPromocion.ACTIVA
    return EstadoPromocion.FINALIZADA


class PromocionService:
    def __init__(self, db: Session):
        self._db = db
        self._promociones = PromocionRepository(db)
        self._productos = ProductoLecturaRepository(db)

    def listar(self) -> list[PromocionListadoOut]:
        hoy = date.today()
        return [self._a_listado(p, hoy) for p in self._promociones.listar()]

    def obtener(self, promocion_id: int) -> PromocionDetalleOut:
        promocion = self._promociones.obtener_por_id(promocion_id)
        if promocion is None:
            raise PromocionNoEncontradaError
        return self._a_detalle(promocion, date.today())

    def crear(self, datos: CrearPromocionRequest) -> PromocionDetalleOut:
        self._validar_rango(datos.fecha_inicio, datos.fecha_fin)
        productos = self._resolver_productos(datos.producto_ids)
        if self._promociones.existe_solapamiento(list(productos.keys()), datos.fecha_inicio, datos.fecha_fin):
            raise SolapamientoError

        promocion = Promocion(
            nombre=datos.nombre.strip(),
            porcentaje_descuento=Decimal(str(datos.porcentaje_descuento)),
            fecha_inicio=datos.fecha_inicio,
            fecha_fin=datos.fecha_fin,
            activa=True,
            productos=list(productos.values()),
        )
        self._promociones.crear(promocion)
        return self._a_detalle(promocion, date.today())

    def editar(self, promocion_id: int, datos: EditarPromocionRequest) -> PromocionDetalleOut:
        promocion = self._promociones.obtener_por_id_bloqueado(promocion_id)
        if promocion is None:
            raise PromocionNoEncontradaError

        hoy = date.today()
        if _calcular_estado(promocion, hoy) in _ESTADOS_NO_EDITABLES:
            raise PromocionNoEditableError

        self._validar_rango(datos.fecha_inicio, datos.fecha_fin)
        productos = self._resolver_productos(datos.producto_ids)
        if self._promociones.existe_solapamiento(
            list(productos.keys()), datos.fecha_inicio, datos.fecha_fin, excluir_promocion_id=promocion.id
        ):
            raise SolapamientoError

        promocion.nombre = datos.nombre.strip()
        promocion.porcentaje_descuento = Decimal(str(datos.porcentaje_descuento))
        promocion.fecha_inicio = datos.fecha_inicio
        promocion.fecha_fin = datos.fecha_fin
        promocion.productos = list(productos.values())
        self._promociones.guardar()
        return self._a_detalle(promocion, hoy)

    def desactivar(self, promocion_id: int) -> PromocionDetalleOut:
        promocion = self._promociones.obtener_por_id_bloqueado(promocion_id)
        if promocion is None:
            raise PromocionNoEncontradaError
        promocion.activa = False
        self._promociones.guardar()
        return self._a_detalle(promocion, date.today())

    @staticmethod
    def _validar_rango(fecha_inicio: date, fecha_fin: date) -> None:
        if fecha_fin < fecha_inicio:
            raise RangoFechaInvalidoError

    def _resolver_productos(self, producto_ids: list[int]) -> dict[int, Producto]:
        ids_unicos = set(producto_ids)
        productos = self._productos.get_activos_by_ids(ids_unicos)
        if len(productos) != len(ids_unicos):
            raise ProductoNoEncontradoError
        return productos

    @staticmethod
    def _a_listado(promocion: Promocion, hoy: date) -> PromocionListadoOut:
        return PromocionListadoOut(
            id=promocion.id,
            nombre=promocion.nombre,
            porcentaje_descuento=promocion.porcentaje_descuento,
            fecha_inicio=promocion.fecha_inicio,
            fecha_fin=promocion.fecha_fin,
            estado=_calcular_estado(promocion, hoy).value,
            cantidad_productos=len(promocion.productos),
            fecha_creacion=promocion.fecha_creacion,
        )

    @staticmethod
    def _a_detalle(promocion: Promocion, hoy: date) -> PromocionDetalleOut:
        return PromocionDetalleOut(
            id=promocion.id,
            nombre=promocion.nombre,
            porcentaje_descuento=promocion.porcentaje_descuento,
            fecha_inicio=promocion.fecha_inicio,
            fecha_fin=promocion.fecha_fin,
            estado=_calcular_estado(promocion, hoy).value,
            activa=promocion.activa,
            fecha_creacion=promocion.fecha_creacion,
            productos=[
                ProductoPromocionOut(
                    id=p.id, nombre=p.nombre, imagen_principal_url=p.imagen_principal_url
                )
                for p in promocion.productos
            ],
        )
