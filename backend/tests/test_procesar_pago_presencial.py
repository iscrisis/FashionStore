"""Pruebas de CU25 -- Procesar pago presencial (Cajero).

Arma el escenario vía los endpoints REALES de CU24 (crear la Venta
DIRECTA/PENDIENTE_PAGO, y desde una Reserva LISTA_PARA_CAJA creada
directamente en la base -- mismo patrón ya usado por
test_registrar_venta_presencial.py) y prueba CU25 sobre esas ventas ya
creadas.

Énfasis en: el total se recalcula/verifica SIEMPRE desde los VentaDetalle ya
congelados (nunca desde Angular), EFECTIVO exige monto_recibido >= total y
calcula el cambio, una venta DIRECTA descuenta SOLO stock_actual (nunca
stock_reservado), una venta RESERVA descuenta AMBOS, la Reserva pasa a
ATENDIDA solo tras el pago (nunca antes), una Venta ya PAGADA no puede
cobrarse dos veces, y nada de esto ocurre si el Cajero cierra sin pagar.
"""

import uuid
from datetime import date, time
from decimal import Decimal

from tests.test_crear_reserva_prendas import _auth_headers, _create_test_user, _delete_test_user
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_variante import ProductoVariante
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.stock_sucursal import StockSucursal
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva, Reserva, ReservaDetalle
from modules.P5_ComprasVentasYPagos.Models.pago import Pago
from modules.P5_ComprasVentasYPagos.Models.venta import Venta

client = TestClient(app)


class _EscenarioPagoPresencial:
    """Un producto con 2 variantes en la sucursal del Cajero:
      - variante_a: cantidad=9, stock_reservado=3 -- para una venta DIRECTA
        de 2 unidades (disponible=6, nunca toca el reservado).
      - variante_b: cantidad=9, stock_reservado=3 -- con una Reserva
        LISTA_PARA_CAJA de 2 unidades de esta variante (mismo ejemplo
        numérico del requerimiento: tras pagar, actual=7, reservado=1)."""

    def __init__(self):
        self.db = SessionLocal()
        sufijo = uuid.uuid4().hex[:8]

        self.proveedor = Proveedor(
            razon_social=f"Proveedor {sufijo}",
            nombre_contacto="Ana",
            correo=f"ana-{sufijo}@textiles.com",
            telefono="70011111",
            is_active=True,
        )
        self.categoria = Categoria(nombre=f"Categoria {sufijo}", is_active=True)
        self.temporada = Temporada(
            nombre=f"Temporada {sufijo}", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 3, 31), is_active=True
        )
        self.talla_a = Talla(nombre=f"A-{sufijo}", is_active=True)
        self.talla_b = Talla(nombre=f"B-{sufijo}", is_active=True)
        self.color = Color(nombre=f"Negro-{sufijo}", is_active=True)
        self.ciudad = Ciudad(nombre=f"Ciudad {sufijo}", departamento="Depto", is_active=True)
        self.db.add_all(
            [self.proveedor, self.categoria, self.temporada, self.talla_a, self.talla_b, self.color, self.ciudad]
        )
        self.db.commit()

        self.coleccion = Coleccion(nombre=f"Coleccion {sufijo}", temporada_id=self.temporada.id, is_active=True)
        self.sucursal = Sucursal(
            nombre=f"Sucursal {sufijo}", ciudad_id=self.ciudad.id, direccion="Av. Uno 1", telefono="70022222", is_active=True
        )
        self.db.add_all([self.coleccion, self.sucursal])
        self.db.commit()

        self.producto = Producto(
            nombre=f"Chompa Andina {sufijo}",
            proveedor_id=self.proveedor.id,
            categoria_id=self.categoria.id,
            temporada_id=self.temporada.id,
            coleccion_id=self.coleccion.id,
            precio_venta=Decimal("100.00"),
            is_active=True,
            tallas=[self.talla_a, self.talla_b],
            colores=[self.color],
        )
        self.db.add(self.producto)
        self.db.commit()
        self.db.refresh(self.producto)

        self.variante_a = ProductoVariante(
            producto_id=self.producto.id, talla_id=self.talla_a.id, color_id=self.color.id, is_active=True
        )
        self.variante_b = ProductoVariante(
            producto_id=self.producto.id, talla_id=self.talla_b.id, color_id=self.color.id, is_active=True
        )
        self.db.add_all([self.variante_a, self.variante_b])
        self.db.commit()
        self.db.refresh(self.variante_a)
        self.db.refresh(self.variante_b)

        self.db.add_all(
            [
                StockSucursal(sucursal_id=self.sucursal.id, producto_variante_id=self.variante_a.id, cantidad=9, stock_reservado=3),
                StockSucursal(sucursal_id=self.sucursal.id, producto_variante_id=self.variante_b.id, cantidad=9, stock_reservado=3),
            ]
        )
        self.db.commit()

        self.cajero = _create_test_user(RolUsuario.CAJERO, sucursal_id=self.sucursal.id)
        self.cliente = _create_test_user(RolUsuario.CLIENTE)

        self.reserva = Reserva(
            codigo_reserva=f"RS-TEST-{sufijo}",
            cliente_id=self.cliente.id,
            sucursal_id=self.sucursal.id,
            fecha_reserva=date(2026, 1, 10),
            hora_inicio=time(10, 0),
            estado_general=EstadoReserva.LISTA_PARA_CAJA,
        )
        self.db.add(self.reserva)
        self.db.commit()
        self.db.refresh(self.reserva)

        self.db.add(
            ReservaDetalle(
                reserva_id=self.reserva.id,
                producto_variante_id=self.variante_b.id,
                cantidad=2,
                estado=EstadoReserva.LISTA_PARA_CAJA,
            )
        )
        self.db.commit()

    def headers(self) -> dict:
        return _auth_headers(self.cajero)

    def crear_venta_directa(self, cantidad: int = 2) -> dict:
        response = client.post(
            "/api/v1/ventas-presenciales/directa",
            headers=self.headers(),
            json={"items": [{"producto_variante_id": self.variante_a.id, "cantidad": cantidad}]},
        )
        assert response.status_code == 201, response.text
        return response.json()

    def crear_venta_desde_reserva(self) -> dict:
        response = client.post(
            f"/api/v1/ventas-presenciales/desde-reserva/{self.reserva.id}", headers=self.headers()
        )
        assert response.status_code == 201, response.text
        return response.json()

    def _fila_stock(self, variante_id: int) -> StockSucursal | None:
        db = SessionLocal()
        try:
            return (
                db.query(StockSucursal)
                .filter(StockSucursal.sucursal_id == self.sucursal.id, StockSucursal.producto_variante_id == variante_id)
                .first()
            )
        finally:
            db.close()

    def stock_actual(self, variante_id: int) -> int:
        fila = self._fila_stock(variante_id)
        return fila.cantidad if fila else 0

    def stock_reservado(self, variante_id: int) -> int:
        fila = self._fila_stock(variante_id)
        return fila.stock_reservado if fila else 0

    def reserva_estado_actual(self) -> str:
        db = SessionLocal()
        try:
            reserva = db.get(Reserva, self.reserva.id)
            return reserva.estado_general.value
        finally:
            db.close()

    def venta_estado_actual(self, venta_id: int) -> str:
        db = SessionLocal()
        try:
            venta = db.get(Venta, venta_id)
            return venta.estado.value
        finally:
            db.close()

    def cleanup(self) -> None:
        try:
            variante_ids = [self.variante_a.id, self.variante_b.id]
            ventas = self.db.query(Venta).filter(Venta.cajero_id == self.cajero.id).all()
            self.db.query(Pago).filter(Pago.venta_id.in_([v.id for v in ventas])).delete(synchronize_session=False)
            self.db.commit()
            for v in ventas:
                self.db.delete(v)
            self.db.commit()

            self.db.query(ReservaDetalle).filter(ReservaDetalle.reserva_id == self.reserva.id).delete(
                synchronize_session=False
            )
            self.db.commit()
            self.db.delete(self.reserva)
            self.db.commit()

            _delete_test_user(self.cajero.id)
            _delete_test_user(self.cliente.id)

            self.db.query(StockSucursal).filter(StockSucursal.producto_variante_id.in_(variante_ids)).delete(
                synchronize_session=False
            )
            self.db.commit()
            for variante in (self.variante_a, self.variante_b):
                obj = self.db.get(ProductoVariante, variante.id)
                if obj is not None:
                    self.db.delete(obj)
            self.db.commit()
            self.db.delete(self.producto)
            self.db.commit()
            self.db.delete(self.sucursal)
            self.db.delete(self.coleccion)
            self.db.delete(self.temporada)
            self.db.delete(self.categoria)
            self.db.delete(self.talla_a)
            self.db.delete(self.talla_b)
            self.db.delete(self.color)
            self.db.delete(self.proveedor)
            self.db.commit()
            self.db.delete(self.ciudad)
            self.db.commit()
        finally:
            self.db.close()


def _confirmar(escenario: _EscenarioPagoPresencial, venta_id: int, payload: dict):
    return client.post(
        f"/api/v1/pagos-presenciales/{venta_id}/confirmar", headers=escenario.headers(), json=payload
    )


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_confirmar_sin_token_es_rechazado():
    response = client.post("/api/v1/pagos-presenciales/1/confirmar", json={"metodo_pago": "QR"})
    assert response.status_code == 401


def test_otro_rol_no_puede_confirmar_pago():
    escenario = _EscenarioPagoPresencial()
    encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal.id)
    try:
        venta = escenario.crear_venta_directa()
        response = client.post(
            f"/api/v1/pagos-presenciales/{venta['id']}/confirmar",
            headers=_auth_headers(encargado),
            json={"metodo_pago": "QR"},
        )
        assert response.status_code == 403
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_cajero_de_otra_sucursal_no_puede_confirmar():
    escenario = _EscenarioPagoPresencial()
    otra_sucursal = Sucursal(
        nombre="Otra", ciudad_id=escenario.ciudad.id, direccion="Av. Otra", telefono="70099999", is_active=True
    )
    escenario.db.add(otra_sucursal)
    escenario.db.commit()
    escenario.db.refresh(otra_sucursal)
    cajero_b = _create_test_user(RolUsuario.CAJERO, sucursal_id=otra_sucursal.id)
    try:
        venta = escenario.crear_venta_directa()
        response = client.post(
            f"/api/v1/pagos-presenciales/{venta['id']}/confirmar",
            headers=_auth_headers(cajero_b),
            json={"metodo_pago": "QR"},
        )
        assert response.status_code == 404
    finally:
        _delete_test_user(cajero_b.id)
        escenario.db.delete(otra_sucursal)
        escenario.db.commit()
        escenario.cleanup()


# --------------------------------------------------------------------------
# EFECTIVO: exige monto_recibido >= total; calcula el cambio.
# --------------------------------------------------------------------------


def test_efectivo_con_monto_insuficiente_es_rechazado():
    escenario = _EscenarioPagoPresencial()
    try:
        venta = escenario.crear_venta_directa()  # total = 200 (2 x 100)
        response = _confirmar(escenario, venta["id"], {"metodo_pago": "EFECTIVO", "monto_recibido": 150})
        assert response.status_code == 422
        assert escenario.venta_estado_actual(venta["id"]) == "PENDIENTE_PAGO"
    finally:
        escenario.cleanup()


def test_efectivo_calcula_el_cambio_correctamente():
    escenario = _EscenarioPagoPresencial()
    try:
        venta = escenario.crear_venta_directa()  # total = 200
        response = _confirmar(escenario, venta["id"], {"metodo_pago": "EFECTIVO", "monto_recibido": 250})
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["metodo_pago"] == "EFECTIVO"
        assert Decimal(str(body["monto_recibido"])) == Decimal("250.00")
        assert Decimal(str(body["cambio"])) == Decimal("50.00")

        db = SessionLocal()
        try:
            pago = db.query(Pago).filter(Pago.venta_id == venta["id"]).one()
            assert pago.estado.value == "PAGADO"
            assert pago.cajero_id == escenario.cajero.id
            assert pago.monto_recibido == Decimal("250.00")
            assert pago.cambio == Decimal("50.00")
        finally:
            db.close()
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Venta DIRECTA: descuenta SOLO stock_actual.
# --------------------------------------------------------------------------


def test_venta_directa_pagada_descuenta_solo_stock_actual():
    escenario = _EscenarioPagoPresencial()
    try:
        venta = escenario.crear_venta_directa(cantidad=2)  # variante_a: actual=9, reservado=3
        response = _confirmar(escenario, venta["id"], {"metodo_pago": "QR"})
        assert response.status_code == 201, response.text

        assert escenario.stock_actual(escenario.variante_a.id) == 7  # 9 - 2
        assert escenario.stock_reservado(escenario.variante_a.id) == 3  # SIN CAMBIOS
        assert escenario.venta_estado_actual(venta["id"]) == "PAGADA"
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Venta RESERVA: descuenta stock_actual Y stock_reservado; la Reserva pasa a
# ATENDIDA solo tras el pago.
# --------------------------------------------------------------------------


def test_venta_desde_reserva_pagada_descuenta_actual_y_reservado_y_atiende_la_reserva():
    escenario = _EscenarioPagoPresencial()
    try:
        venta = escenario.crear_venta_desde_reserva()  # variante_b: actual=9, reservado=3, cantidad=2
        assert escenario.reserva_estado_actual() == "LISTA_PARA_CAJA"  # antes del pago

        response = _confirmar(escenario, venta["id"], {"metodo_pago": "TARJETA", "tipo_tarjeta": "CREDITO"})
        assert response.status_code == 201, response.text

        assert escenario.stock_actual(escenario.variante_b.id) == 7  # 9 - 2
        assert escenario.stock_reservado(escenario.variante_b.id) == 1  # 3 - 2
        assert escenario.venta_estado_actual(venta["id"]) == "PAGADA"
        assert escenario.reserva_estado_actual() == "ATENDIDA"  # SOLO después del pago

        db = SessionLocal()
        try:
            pago = db.query(Pago).filter(Pago.venta_id == venta["id"]).one()
            assert pago.tipo_tarjeta.value == "CREDITO"
        finally:
            db.close()
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Idempotencia: una Venta ya PAGADA no puede cobrarse otra vez.
# --------------------------------------------------------------------------


def test_venta_ya_pagada_no_puede_cobrarse_dos_veces():
    escenario = _EscenarioPagoPresencial()
    try:
        venta = escenario.crear_venta_directa(cantidad=1)
        primera = _confirmar(escenario, venta["id"], {"metodo_pago": "QR"})
        assert primera.status_code == 201

        stock_tras_primer_pago = escenario.stock_actual(escenario.variante_a.id)

        segunda = _confirmar(escenario, venta["id"], {"metodo_pago": "QR"})
        assert segunda.status_code == 422

        # No se descontó una segunda vez.
        assert escenario.stock_actual(escenario.variante_a.id) == stock_tras_primer_pago
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Cerrar sin pagar: la Venta sigue PENDIENTE_PAGO, nada cambia (aquí:
# simplemente nunca se llama a confirmar -- el estado natural tras CU24).
# --------------------------------------------------------------------------


def test_venta_sin_confirmar_sigue_pendiente_de_pago_y_no_toca_nada():
    escenario = _EscenarioPagoPresencial()
    try:
        venta = escenario.crear_venta_directa(cantidad=2)
        assert escenario.venta_estado_actual(venta["id"]) == "PENDIENTE_PAGO"
        assert escenario.stock_actual(escenario.variante_a.id) == 9
        assert escenario.stock_reservado(escenario.variante_a.id) == 3
    finally:
        escenario.cleanup()
