"""Pruebas de CU23 -- Procesar pago electrónico (Cliente).

Arma el escenario vía los endpoints REALES de CU21 (carrito) y CU22 (crear
la Venta PENDIENTE_PAGO), igual que test_realizar_compra_digital.py. Stripe
mismo NUNCA se llama de verdad en estos tests -- se reemplazan
`crear_checkout_session`/`obtener_checkout_session` (los dos únicos puntos
donde CU23 toca la red, ver app/integrations/stripe_client.py) por dobles
que simulan las respuestas de Stripe, exactamente lo que se recomienda
probar en un test de integración: la lógica de negocio de CU23 (quién puede
pagar qué, cuándo se descuenta stock, cuándo se limpia el carrito, la
idempotencia), no la disponibilidad real de la red de Stripe.

Énfasis en: FastAPI (nunca Angular) decide si un pago se completó, el monto
cobrado sale SIEMPRE de Venta.total, verificar_pago es idempotente (no
duplica descuento de stock ni limpieza del carrito), un pago cancelado o
fallido NUNCA mueve la Venta de PENDIENTE_PAGO (permite reintentar), y solo
se elimina del carrito lo que formó parte de la Venta pagada.
"""

import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

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
from modules.P5_ComprasVentasYPagos.Models.carrito import Carrito, CarritoItem
from modules.P5_ComprasVentasYPagos.Models.pago import Pago
from modules.P5_ComprasVentasYPagos.Models.venta import Venta

client = TestClient(app)

_SERVICE_PATH = "modules.P5_ComprasVentasYPagos.CU23_ProcesarPagoElectronico.service"


def _fake_session(**overrides) -> SimpleNamespace:
    base = {
        "id": f"cs_test_{uuid.uuid4().hex[:12]}",
        "url": "https://checkout.stripe.com/test/fake-session",
        "payment_status": "unpaid",
        "payment_intent": None,
        "status": "open",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class _EscenarioPago:
    """Un producto con 2 variantes (A y B), una sucursal con stock de sobra
    para ambas. El carrito del Cliente tiene item_a (SELECCIONADO -> pasa a
    la Venta) e item_b (NO seleccionado -> nunca debe tocarse). La Venta
    (CU22) ya queda creada, PENDIENTE_PAGO, con solo item_a."""

    def __init__(self, *, stock_inicial: int = 5):
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
            nombre=f"Temporada {sufijo}",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 3, 31),
            is_active=True,
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
            nombre=f"Sucursal {sufijo}",
            ciudad_id=self.ciudad.id,
            direccion="Av. Siempre Viva 123",
            telefono="70022222",
            is_active=True,
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
                StockSucursal(sucursal_id=self.sucursal.id, producto_variante_id=self.variante_a.id, cantidad=stock_inicial),
                StockSucursal(sucursal_id=self.sucursal.id, producto_variante_id=self.variante_b.id, cantidad=stock_inicial),
            ]
        )
        self.db.commit()

        self.cliente = _create_test_user(RolUsuario.CLIENTE)

        r1 = client.post(
            "/api/v1/carrito/items", headers=self.headers(), json={"producto_variante_id": self.variante_a.id}
        )
        self.item_a_id = r1.json()["items"][0]["item_id"]
        r2 = client.post(
            "/api/v1/carrito/items", headers=self.headers(), json={"producto_variante_id": self.variante_b.id}
        )
        self.item_b_id = next(
            i["item_id"] for i in r2.json()["items"] if i["producto_variante_id"] == self.variante_b.id
        )
        client.patch(
            f"/api/v1/carrito/items/{self.item_b_id}", headers=self.headers(), json={"seleccionado": False}
        )

        r3 = client.post(
            "/api/v1/compra-digital", headers=self.headers(), json={"sucursal_id": self.sucursal.id}
        )
        assert r3.status_code == 201, r3.text
        self.venta = r3.json()
        self.venta_id = self.venta["id"]

    def headers(self) -> dict:
        return _auth_headers(self.cliente)

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

    def carrito_item_ids(self) -> set[int]:
        respuesta = client.get("/api/v1/carrito", headers=self.headers())
        return {item["item_id"] for item in respuesta.json()["items"]}

    def crear_checkout(self) -> str:
        """Crea el Checkout (mockeado) y devuelve el session_id creado."""
        with patch(f"{_SERVICE_PATH}.crear_checkout_session", return_value=_fake_session()) as mock_crear:
            response = client.post(
                "/api/v1/pagos/checkout", headers=self.headers(), json={"venta_id": self.venta_id}
            )
        assert response.status_code == 201, response.text
        return mock_crear.return_value.id

    def cleanup(self) -> None:
        try:
            variante_ids = [self.variante_a.id, self.variante_b.id]
            ventas = self.db.query(Venta).filter(Venta.cliente_id == self.cliente.id).all()
            for venta in ventas:
                self.db.delete(venta)  # cascada: VentaDetalle + Pago (ON DELETE CASCADE)
            self.db.commit()
            self.db.query(CarritoItem).filter(CarritoItem.producto_variante_id.in_(variante_ids)).delete(
                synchronize_session=False
            )
            self.db.commit()
            self.db.query(Carrito).filter(Carrito.cliente_id == self.cliente.id).delete(synchronize_session=False)
            self.db.commit()
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


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_checkout_sin_token_es_rechazado():
    response = client.post("/api/v1/pagos/checkout", json={"venta_id": 1})
    assert response.status_code == 401


def test_verificar_sin_token_es_rechazado():
    response = client.post("/api/v1/pagos/verificar", json={"session_id": "cs_test_x"})
    assert response.status_code == 401


# --------------------------------------------------------------------------
# 1/2. VT PENDIENTE_PAGO crea Checkout Session con el monto de Venta.total.
# --------------------------------------------------------------------------


def test_crear_checkout_crea_pago_pendiente_con_el_monto_de_la_venta():
    escenario = _EscenarioPago()
    try:
        sesion_falsa = _fake_session()
        with patch(f"{_SERVICE_PATH}.crear_checkout_session", return_value=sesion_falsa) as mock_crear:
            response = client.post(
                "/api/v1/pagos/checkout", headers=escenario.headers(), json={"venta_id": escenario.venta_id}
            )
        assert response.status_code == 201
        assert response.json()["checkout_url"] == sesion_falsa.url

        # El monto pasado a Stripe fue EXACTAMENTE Venta.total (Decimal, no
        # un valor arbitrario) -- nunca algo que pudiera enviar Angular.
        _, kwargs = mock_crear.call_args
        assert kwargs["monto"] == Decimal(str(escenario.venta["total"]))

        db = SessionLocal()
        try:
            pago = db.query(Pago).filter(Pago.stripe_checkout_session_id == sesion_falsa.id).one()
            assert pago.estado.value == "PENDIENTE"
            assert pago.monto == Decimal(str(escenario.venta["total"]))
            assert pago.venta_id == escenario.venta_id
        finally:
            db.close()
    finally:
        escenario.cleanup()


def test_checkout_con_stock_insuficiente_es_rechazado():
    # El stock se agota DESPUÉS de confirmar la compra (CU22) -- CU21 ya
    # impide agregar al carrito con stock 0, así que ese no es el caso real
    # a cubrir aquí: lo real es que la disponibilidad cambie entre CU22 y
    # el intento de pago, y CU23 debe volver a validarla, nunca confiar en
    # lo que ya se validó antes.
    escenario = _EscenarioPago(stock_inicial=5)
    try:
        db = SessionLocal()
        try:
            fila = (
                db.query(StockSucursal)
                .filter(
                    StockSucursal.sucursal_id == escenario.sucursal.id,
                    StockSucursal.producto_variante_id == escenario.variante_a.id,
                )
                .one()
            )
            fila.cantidad = 0
            db.commit()
        finally:
            db.close()

        response = client.post(
            "/api/v1/pagos/checkout", headers=escenario.headers(), json={"venta_id": escenario.venta_id}
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 5/6/7/8. FastAPI verifica Stripe antes de marcar PAGADA; descuenta SOLO
# lo comprado; limpia del carrito SOLO lo comprado; lo no seleccionado
# permanece.
# --------------------------------------------------------------------------


def test_verificar_pago_exitoso_marca_pagada_descuenta_stock_y_limpia_solo_lo_comprado():
    escenario = _EscenarioPago(stock_inicial=5)
    try:
        session_id = escenario.crear_checkout()

        sesion_pagada = _fake_session(
            id=session_id, payment_status="paid", payment_intent="pi_test_123", status="complete"
        )
        with patch(f"{_SERVICE_PATH}.obtener_checkout_session", return_value=sesion_pagada):
            response = client.post(
                "/api/v1/pagos/verificar", headers=escenario.headers(), json={"session_id": session_id}
            )
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "PAGADA"
        assert body["codigo_venta"] == escenario.venta["codigo_venta"]
        assert Decimal(str(body["total"])) == Decimal(str(escenario.venta["total"]))
        assert body["sucursal"]["id"] == escenario.sucursal.id

        # Stock: SOLO la variante comprada baja, exactamente 1 unidad.
        assert escenario.stock_actual(escenario.variante_a.id) == 4
        assert escenario.stock_reservado(escenario.variante_a.id) == 0
        assert escenario.stock_actual(escenario.variante_b.id) == 5

        # Carrito: el item comprado desaparece; el no seleccionado queda.
        item_ids = escenario.carrito_item_ids()
        assert escenario.item_a_id not in item_ids
        assert escenario.item_b_id in item_ids

        db = SessionLocal()
        try:
            venta = db.get(Venta, escenario.venta_id)
            assert venta.estado.value == "PAGADA"
            pago = db.query(Pago).filter(Pago.stripe_checkout_session_id == session_id).one()
            assert pago.estado.value == "PAGADO"
            assert pago.stripe_payment_intent_id == "pi_test_123"
            assert pago.fecha_confirmacion is not None
        finally:
            db.close()
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 11. Refrescar/verificar dos veces NO duplica el descuento de stock.
# --------------------------------------------------------------------------


def test_verificar_pago_es_idempotente():
    escenario = _EscenarioPago(stock_inicial=5)
    try:
        session_id = escenario.crear_checkout()
        sesion_pagada = _fake_session(id=session_id, payment_status="paid", payment_intent="pi_test_456", status="complete")

        with patch(f"{_SERVICE_PATH}.obtener_checkout_session", return_value=sesion_pagada):
            primera = client.post(
                "/api/v1/pagos/verificar", headers=escenario.headers(), json={"session_id": session_id}
            )
            segunda = client.post(
                "/api/v1/pagos/verificar", headers=escenario.headers(), json={"session_id": session_id}
            )
        assert primera.status_code == 200
        assert segunda.status_code == 200
        assert primera.json() == segunda.json()

        # Un solo descuento, no dos.
        assert escenario.stock_actual(escenario.variante_a.id) == 4
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 9/10. Cancelar/fallar el pago NO toca stock ni carrito y permite
# reintentar.
# --------------------------------------------------------------------------


def test_pago_no_completado_no_cambia_stock_ni_carrito_y_permite_reintentar():
    escenario = _EscenarioPago(stock_inicial=5)
    try:
        session_id = escenario.crear_checkout()

        sesion_cancelada = _fake_session(id=session_id, payment_status="unpaid", status="expired")
        with patch(f"{_SERVICE_PATH}.obtener_checkout_session", return_value=sesion_cancelada):
            response = client.post(
                "/api/v1/pagos/verificar", headers=escenario.headers(), json={"session_id": session_id}
            )
        assert response.status_code == 422

        assert escenario.stock_actual(escenario.variante_a.id) == 5
        item_ids = escenario.carrito_item_ids()
        assert escenario.item_a_id in item_ids
        assert escenario.item_b_id in item_ids

        db = SessionLocal()
        try:
            venta = db.get(Venta, escenario.venta_id)
            assert venta.estado.value == "PENDIENTE_PAGO"
        finally:
            db.close()

        # Reintentar: la Venta sigue admitiendo un Checkout nuevo.
        nuevo_session_id = escenario.crear_checkout()
        assert nuevo_session_id != session_id
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 12. Otro cliente no puede pagar (ni verificar) una Venta ajena.
# --------------------------------------------------------------------------


def test_otro_cliente_no_puede_pagar_una_venta_ajena():
    escenario = _EscenarioPago()
    cliente_b = _create_test_user(RolUsuario.CLIENTE)
    try:
        checkout_ajeno = client.post(
            "/api/v1/pagos/checkout", headers=_auth_headers(cliente_b), json={"venta_id": escenario.venta_id}
        )
        assert checkout_ajeno.status_code == 404

        session_id = escenario.crear_checkout()
        verificar_ajeno = client.post(
            "/api/v1/pagos/verificar", headers=_auth_headers(cliente_b), json={"session_id": session_id}
        )
        assert verificar_ajeno.status_code == 404
    finally:
        _delete_test_user(cliente_b.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# Auditoría puntual (stock_reservado NUNCA debe bajar por una compra
# digital): una variante con una reserva previa (CU17) ya cargada en
# stock_reservado -- comprar digitalmente (CU23) descuenta SOLO
# stock_actual.
#
#   Antes:  stock_actual=9, stock_reservado=3, disponible=6
#   Compra digital de 2 unidades
#   Después esperado: stock_actual=7, stock_reservado=3 (SIN CAMBIOS), disponible=4
# --------------------------------------------------------------------------


def test_auditoria_compra_digital_no_reduce_stock_reservado_existente():
    db = SessionLocal()
    sufijo = uuid.uuid4().hex[:8]

    proveedor = Proveedor(
        razon_social=f"Proveedor {sufijo}",
        nombre_contacto="Ana",
        correo=f"ana-{sufijo}@textiles.com",
        telefono="70011111",
        is_active=True,
    )
    categoria = Categoria(nombre=f"Categoria {sufijo}", is_active=True)
    temporada = Temporada(
        nombre=f"Temporada {sufijo}", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 3, 31), is_active=True
    )
    talla = Talla(nombre=f"T-{sufijo}", is_active=True)
    color = Color(nombre=f"C-{sufijo}", is_active=True)
    ciudad = Ciudad(nombre=f"Ciudad {sufijo}", departamento="Depto", is_active=True)
    db.add_all([proveedor, categoria, temporada, talla, color, ciudad])
    db.commit()

    coleccion = Coleccion(nombre=f"Coleccion {sufijo}", temporada_id=temporada.id, is_active=True)
    sucursal = Sucursal(
        nombre=f"Sucursal {sufijo}", ciudad_id=ciudad.id, direccion="Av. Auditoria 1", telefono="70022222", is_active=True
    )
    db.add_all([coleccion, sucursal])
    db.commit()

    producto = Producto(
        nombre=f"Producto Auditoria {sufijo}",
        proveedor_id=proveedor.id,
        categoria_id=categoria.id,
        temporada_id=temporada.id,
        coleccion_id=coleccion.id,
        precio_venta=Decimal("50.00"),
        is_active=True,
        tallas=[talla],
        colores=[color],
    )
    db.add(producto)
    db.commit()
    db.refresh(producto)

    variante = ProductoVariante(producto_id=producto.id, talla_id=talla.id, color_id=color.id, is_active=True)
    db.add(variante)
    db.commit()
    db.refresh(variante)

    # Precondición EXACTA del ejemplo de la auditoría: ya existe una reserva
    # (CU17) comprometiendo 3 unidades -- simulada directo en la fila de
    # stock, sin pasar por CU17 (no es su lógica lo que se audita aquí).
    fila_stock = StockSucursal(sucursal_id=sucursal.id, producto_variante_id=variante.id, cantidad=9, stock_reservado=3)
    db.add(fila_stock)
    db.commit()

    cliente = _create_test_user(RolUsuario.CLIENTE)

    try:
        headers = _auth_headers(cliente)

        antes = db.query(StockSucursal).filter(StockSucursal.id == fila_stock.id).first()
        # Tupla de valores planos (no el objeto ORM): `antes` queda en el
        # identity map de esta Session, así que un `expire_all()` posterior
        # también lo invalidaría a él -- capturar los números ahora es lo
        # único que garantiza que el "antes" impreso más abajo sea realmente
        # el de antes, no una relectura post-compra del mismo objeto.
        antes_valores = (antes.cantidad, antes.stock_reservado)
        assert antes_valores == (9, 3)

        # Compra digital de 2 unidades -- dos items individuales de CU21
        # (cada uno es una unidad concreta), ambos seleccionados por defecto.
        r1 = client.post("/api/v1/carrito/items", headers=headers, json={"producto_variante_id": variante.id})
        assert r1.status_code == 201, r1.text
        r2 = client.post("/api/v1/carrito/items", headers=headers, json={"producto_variante_id": variante.id})
        assert r2.status_code == 201, r2.text

        venta_resp = client.post("/api/v1/compra-digital", headers=headers, json={"sucursal_id": sucursal.id})
        assert venta_resp.status_code == 201, venta_resp.text
        venta_id = venta_resp.json()["id"]

        sesion_creada = _fake_session()
        with patch(f"{_SERVICE_PATH}.crear_checkout_session", return_value=sesion_creada):
            checkout_resp = client.post("/api/v1/pagos/checkout", headers=headers, json={"venta_id": venta_id})
        assert checkout_resp.status_code == 201, checkout_resp.text

        sesion_pagada = _fake_session(
            id=sesion_creada.id, payment_status="paid", payment_intent="pi_test_auditoria", status="complete"
        )
        with patch(f"{_SERVICE_PATH}.obtener_checkout_session", return_value=sesion_pagada):
            verificar_resp = client.post(
                "/api/v1/pagos/verificar", headers=headers, json={"session_id": sesion_creada.id}
            )
        assert verificar_resp.status_code == 200, verificar_resp.text
        assert verificar_resp.json()["estado"] == "PAGADA"

        db.expire_all()
        despues = db.query(StockSucursal).filter(StockSucursal.id == fila_stock.id).first()
        despues_valores = (despues.cantidad, despues.stock_reservado)
        print(
            f"\n[AUDITORÍA CU23] antes: actual={antes_valores[0]} reservado={antes_valores[1]} "
            f"| después: actual={despues_valores[0]} reservado={despues_valores[1]}"
        )
        assert despues_valores[0] == 7, f"stock_actual esperado 7, quedó {despues_valores[0]}"
        assert despues_valores[1] == 3, f"stock_reservado esperado 3 (SIN CAMBIOS), quedó {despues_valores[1]}"
    finally:
        ventas = db.query(Venta).filter(Venta.cliente_id == cliente.id).all()
        for v in ventas:
            db.delete(v)
        db.commit()
        db.query(CarritoItem).filter(CarritoItem.producto_variante_id == variante.id).delete(synchronize_session=False)
        db.commit()
        db.query(Carrito).filter(Carrito.cliente_id == cliente.id).delete(synchronize_session=False)
        db.commit()
        _delete_test_user(cliente.id)
        db.query(StockSucursal).filter(StockSucursal.producto_variante_id == variante.id).delete(
            synchronize_session=False
        )
        db.commit()
        obj = db.get(ProductoVariante, variante.id)
        if obj is not None:
            db.delete(obj)
        db.commit()
        db.delete(producto)
        db.commit()
        db.delete(sucursal)
        db.delete(coleccion)
        db.delete(temporada)
        db.delete(categoria)
        db.delete(talla)
        db.delete(color)
        db.delete(proveedor)
        db.commit()
        db.delete(ciudad)
        db.commit()
        db.close()
