"""Pruebas de CU24 -- Registrar venta presencial (Cajero).

Arma el escenario a mano (producto -> 2 variantes, dos sucursales, un Cajero
ligado a la primera, y una Reserva LISTA_PARA_CAJA creada directamente en la
base -- CU24 solo LEE ese estado, no reimplementa el flujo CU17-20 que ya
tiene su propia suite) -- mismo patrón ya usado por
test_realizar_compra_digital.py y test_usar_carrito_compras.py.

Énfasis en: el Cajero solo ve/usa stock y reservas de SU sucursal, una venta
DIRECTA nunca puede exceder `stock_actual - stock_reservado`, una venta
DESDE RESERVA solo carga los detalles LISTA_PARA_CAJA (nunca los que el
Cliente no se llevó), FastAPI recalcula precio/total siempre, CU24 jamás
toca StockSucursal ni cambia el estado de la Reserva, y nunca duplica una
Venta pendiente para la misma reserva.
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
from modules.P5_ComprasVentasYPagos.Models.venta import Venta

client = TestClient(app)


class _EscenarioVentaPresencial:
    """Un producto con 2 variantes (A y B). Sucursal A (la del Cajero):
    variante_a con cantidad=9/reservado=3 (disponible=6, simula una unidad
    ya comprometida por una reserva), variante_b con cantidad=5/reservado=0
    (libre). Sucursal B (otra, para el caso "reserva de otra sucursal").
    Una Reserva LISTA_PARA_CAJA en sucursal A con 2 detalles: uno
    LISTA_PARA_CAJA (variante_b) y otro ATENDIDA (variante_a, "no la
    compra") -- para probar que solo el primero entra a la venta."""

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
        self.sucursal_a = Sucursal(
            nombre=f"Sucursal A {sufijo}", ciudad_id=self.ciudad.id, direccion="Av. Uno 1", telefono="70022222", is_active=True
        )
        self.sucursal_b = Sucursal(
            nombre=f"Sucursal B {sufijo}", ciudad_id=self.ciudad.id, direccion="Av. Dos 2", telefono="70033333", is_active=True
        )
        self.db.add_all([self.coleccion, self.sucursal_a, self.sucursal_b])
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
                StockSucursal(sucursal_id=self.sucursal_a.id, producto_variante_id=self.variante_a.id, cantidad=9, stock_reservado=3),
                StockSucursal(sucursal_id=self.sucursal_a.id, producto_variante_id=self.variante_b.id, cantidad=5, stock_reservado=0),
            ]
        )
        self.db.commit()

        self.cajero = _create_test_user(RolUsuario.CAJERO, sucursal_id=self.sucursal_a.id)
        self.cliente = _create_test_user(RolUsuario.CLIENTE)

        self.reserva = Reserva(
            codigo_reserva=f"RS-TEST-{sufijo}",
            cliente_id=self.cliente.id,
            sucursal_id=self.sucursal_a.id,
            fecha_reserva=date(2026, 1, 10),
            hora_inicio=time(10, 0),
            estado_general=EstadoReserva.LISTA_PARA_CAJA,
        )
        self.db.add(self.reserva)
        self.db.commit()
        self.db.refresh(self.reserva)

        self.detalle_para_caja = ReservaDetalle(
            reserva_id=self.reserva.id,
            producto_variante_id=self.variante_b.id,
            cantidad=1,
            estado=EstadoReserva.LISTA_PARA_CAJA,
        )
        self.detalle_no_la_compra = ReservaDetalle(
            reserva_id=self.reserva.id,
            producto_variante_id=self.variante_a.id,
            cantidad=1,
            estado=EstadoReserva.ATENDIDA,
        )
        self.db.add_all([self.detalle_para_caja, self.detalle_no_la_compra])
        self.db.commit()

    def headers(self) -> dict:
        return _auth_headers(self.cajero)

    def set_precio(self, precio: Decimal) -> None:
        producto = self.db.get(Producto, self.producto.id)
        producto.precio_venta = precio
        self.db.commit()

    def _fila_stock(self, sucursal_id: int, variante_id: int) -> StockSucursal | None:
        db = SessionLocal()
        try:
            return (
                db.query(StockSucursal)
                .filter(StockSucursal.sucursal_id == sucursal_id, StockSucursal.producto_variante_id == variante_id)
                .first()
            )
        finally:
            db.close()

    def stock_actual(self, variante_id: int, sucursal_id: int | None = None) -> int:
        fila = self._fila_stock(sucursal_id or self.sucursal_a.id, variante_id)
        return fila.cantidad if fila else 0

    def stock_reservado(self, variante_id: int, sucursal_id: int | None = None) -> int:
        fila = self._fila_stock(sucursal_id or self.sucursal_a.id, variante_id)
        return fila.stock_reservado if fila else 0

    def reserva_estado_actual(self) -> str:
        db = SessionLocal()
        try:
            reserva = db.get(Reserva, self.reserva.id)
            return reserva.estado_general.value
        finally:
            db.close()

    def cleanup(self) -> None:
        try:
            variante_ids = [self.variante_a.id, self.variante_b.id]
            ventas = self.db.query(Venta).filter(Venta.reserva_id == self.reserva.id).all()
            for v in ventas:
                self.db.delete(v)
            ventas_cajero = self.db.query(Venta).filter(Venta.cajero_id == self.cajero.id).all()
            for v in ventas_cajero:
                if v.id not in [x.id for x in ventas]:
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
            self.db.delete(self.sucursal_a)
            self.db.delete(self.sucursal_b)
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


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_buscar_productos_sin_token_es_rechazado():
    response = client.get("/api/v1/ventas-presenciales/productos", params={"nombre": "x"})
    assert response.status_code == 401


def test_venta_directa_sin_token_es_rechazado():
    response = client.post("/api/v1/ventas-presenciales/directa", json={"items": [{"producto_variante_id": 1, "cantidad": 1}]})
    assert response.status_code == 401


def test_otro_rol_no_puede_registrar_venta_presencial():
    escenario = _EscenarioVentaPresencial()
    encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal_a.id)
    try:
        response = client.get(
            "/api/v1/ventas-presenciales/productos", params={"nombre": "Chompa"}, headers=_auth_headers(encargado)
        )
        assert response.status_code == 403
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 2/3. Solo ve/usa stock de SU sucursal; disponible = actual - reservado.
# --------------------------------------------------------------------------


def test_buscar_productos_solo_muestra_disponible_de_su_sucursal():
    escenario = _EscenarioVentaPresencial()
    try:
        response = client.get(
            "/api/v1/ventas-presenciales/productos",
            params={"nombre": "Chompa Andina"},
            headers=escenario.headers(),
        )
        assert response.status_code == 200
        por_variante = {r["producto_variante_id"]: r for r in response.json()}
        # variante_a: actual=9, reservado=3 -> disponible=6.
        assert por_variante[escenario.variante_a.id]["disponible"] == 6
        # variante_b: actual=5, reservado=0 -> disponible=5.
        assert por_variante[escenario.variante_b.id]["disponible"] == 5
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 1/5/6/7/15. Venta directa: se puede iniciar, con varias variantes, sin
# cliente, con precio/total recalculados, PRESENCIAL/PENDIENTE_PAGO.
# --------------------------------------------------------------------------


def test_crear_venta_directa_con_varias_variantes_funciona_sin_cliente():
    escenario = _EscenarioVentaPresencial()
    try:
        # El precio sube DESPUÉS de que el Cajero "vio" el producto en la
        # búsqueda -- el total debe reflejar el precio NUEVO.
        escenario.set_precio(Decimal("120.00"))

        response = client.post(
            "/api/v1/ventas-presenciales/directa",
            headers=escenario.headers(),
            json={
                "items": [
                    {"producto_variante_id": escenario.variante_a.id, "cantidad": 2},
                    {"producto_variante_id": escenario.variante_b.id, "cantidad": 1},
                ]
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["tipo"] == "PRESENCIAL"
        assert body["estado"] == "PENDIENTE_PAGO"
        assert body["origen"] == "DIRECTA"
        assert body["reserva"] is None
        assert len(body["detalles"]) == 2
        assert Decimal(str(body["total"])) == Decimal("360.00")  # 3 unidades x 120

        db = SessionLocal()
        try:
            venta = db.query(Venta).filter(Venta.codigo_venta == body["codigo_venta"]).one()
            assert venta.cliente_id is None
            assert venta.cajero_id == escenario.cajero.id
            assert venta.sucursal_id == escenario.sucursal_a.id
        finally:
            db.close()
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 4. Venta directa NO puede exceder disponible (nunca stock reservado).
# --------------------------------------------------------------------------


def test_venta_directa_no_puede_exceder_disponible():
    escenario = _EscenarioVentaPresencial()
    try:
        # variante_a: disponible=6 (9 actual - 3 reservado) -- pedir 7 debe
        # rechazarse, aunque el stock FÍSICO (9) alcanzaría.
        response = client.post(
            "/api/v1/ventas-presenciales/directa",
            headers=escenario.headers(),
            json={"items": [{"producto_variante_id": escenario.variante_a.id, "cantidad": 7}]},
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 8/9. CU24 no modifica stock_actual ni stock_reservado (venta directa).
# --------------------------------------------------------------------------


def test_venta_directa_no_modifica_stock():
    escenario = _EscenarioVentaPresencial()
    try:
        client.post(
            "/api/v1/ventas-presenciales/directa",
            headers=escenario.headers(),
            json={"items": [{"producto_variante_id": escenario.variante_b.id, "cantidad": 2}]},
        )
        assert escenario.stock_actual(escenario.variante_b.id) == 5
        assert escenario.stock_reservado(escenario.variante_b.id) == 0
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 10/11. Reserva LISTA_PARA_CAJA se puede cargar; SOLO los detalles para
# caja entran a la venta.
# --------------------------------------------------------------------------


def test_crear_venta_desde_reserva_carga_solo_detalles_para_caja():
    escenario = _EscenarioVentaPresencial()
    try:
        response = client.post(
            f"/api/v1/ventas-presenciales/desde-reserva/{escenario.reserva.id}",
            headers=escenario.headers(),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["tipo"] == "PRESENCIAL"
        assert body["estado"] == "PENDIENTE_PAGO"
        assert body["origen"] == "RESERVA"
        assert body["reserva"]["codigo_reserva"] == escenario.reserva.codigo_reserva
        assert body["reserva"]["cliente_nombre"] == escenario.cliente.nombre

        variantes_en_venta = {d["variante"]["id"] for d in body["detalles"]}
        assert variantes_en_venta == {escenario.variante_b.id}  # NUNCA variante_a (ATENDIDA, "no la compra")

        db = SessionLocal()
        try:
            venta = db.query(Venta).filter(Venta.codigo_venta == body["codigo_venta"]).one()
            assert venta.cliente_id == escenario.cliente.id
            assert venta.reserva_id == escenario.reserva.id
        finally:
            db.close()
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 8/9 (reserva). CU24 tampoco modifica stock al cargar desde reserva.
# --------------------------------------------------------------------------


def test_venta_desde_reserva_no_modifica_stock():
    escenario = _EscenarioVentaPresencial()
    try:
        client.post(f"/api/v1/ventas-presenciales/desde-reserva/{escenario.reserva.id}", headers=escenario.headers())
        assert escenario.stock_actual(escenario.variante_a.id) == 9
        assert escenario.stock_reservado(escenario.variante_a.id) == 3
        assert escenario.stock_actual(escenario.variante_b.id) == 5
        assert escenario.stock_reservado(escenario.variante_b.id) == 0
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 12. Reserva de otra sucursal es rechazada.
# --------------------------------------------------------------------------


def test_reserva_de_otra_sucursal_es_rechazada():
    escenario = _EscenarioVentaPresencial()
    cajero_b = _create_test_user(RolUsuario.CAJERO, sucursal_id=escenario.sucursal_b.id)
    try:
        response = client.post(
            f"/api/v1/ventas-presenciales/desde-reserva/{escenario.reserva.id}",
            headers=_auth_headers(cajero_b),
        )
        assert response.status_code == 403
    finally:
        _delete_test_user(cajero_b.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 13. Crear venta desde reserva NO cambia la reserva a ATENDIDA.
# --------------------------------------------------------------------------


def test_crear_venta_desde_reserva_no_cambia_estado_de_la_reserva():
    escenario = _EscenarioVentaPresencial()
    try:
        client.post(f"/api/v1/ventas-presenciales/desde-reserva/{escenario.reserva.id}", headers=escenario.headers())
        assert escenario.reserva_estado_actual() == "LISTA_PARA_CAJA"
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 14. No duplicar venta pendiente para la misma reserva.
# --------------------------------------------------------------------------


def test_cargar_venta_dos_veces_no_duplica():
    escenario = _EscenarioVentaPresencial()
    try:
        primera = client.post(
            f"/api/v1/ventas-presenciales/desde-reserva/{escenario.reserva.id}", headers=escenario.headers()
        )
        segunda = client.post(
            f"/api/v1/ventas-presenciales/desde-reserva/{escenario.reserva.id}", headers=escenario.headers()
        )
        assert primera.status_code == 201
        assert segunda.status_code == 201
        assert primera.json()["id"] == segunda.json()["id"]
        assert primera.json()["codigo_venta"] == segunda.json()["codigo_venta"]

        db = SessionLocal()
        try:
            cantidad = db.query(Venta).filter(Venta.reserva_id == escenario.reserva.id).count()
            assert cantidad == 1
        finally:
            db.close()
    finally:
        escenario.cleanup()
