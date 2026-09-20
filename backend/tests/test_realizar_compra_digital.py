"""Pruebas de CU22 -- Realizar compra digital (Cliente).

Arma el escenario a mano (producto -> 2 variantes, una ciudad con dos
sucursales -- una que cubre TODA la compra, otra que solo cubre una de las
dos variantes -- más un Cliente con su carrito ya armado vía los endpoints
reales de CU21) -- mismo patrón ya usado por test_usar_carrito_compras.py.

Énfasis en: CU22 solo usa los items YA seleccionados del carrito propio (los
no seleccionados nunca entran a la compra), una sola sucursal cubre TODA la
compra, FastAPI recalcula precio/total/disponibilidad SIEMPRE en el momento
de confirmar (nunca confía en lo que el Cliente vio antes), el carrito queda
intacto (nada se elimina), y CU22 jamás toca StockSucursal.
"""

import re
import uuid
from datetime import date
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
from modules.P5_ComprasVentasYPagos.Models.carrito import Carrito, CarritoItem
from modules.P5_ComprasVentasYPagos.Models.venta import Venta, VentaDetalle

client = TestClient(app)


class _EscenarioCompra:
    """Un producto con 2 variantes (M y L, mismo color), una ciudad con dos
    sucursales activas:
      - sucursal_full: stock de sobra para AMBAS variantes.
      - sucursal_parcial: solo tiene stock de la variante M -- no puede
        cubrir toda la compra.
    Más un Cliente con su carrito ya armado por los endpoints reales de
    CU21: variante_m y variante_l seleccionadas, variante_m_no_elegida (un
    segundo item, misma variante M, pero deseleccionado) para probar que lo
    no seleccionado nunca entra a la compra."""

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
            nombre=f"Temporada {sufijo}",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 3, 31),
            is_active=True,
        )
        self.talla_m = Talla(nombre=f"M-{sufijo}", is_active=True)
        self.talla_l = Talla(nombre=f"L-{sufijo}", is_active=True)
        self.color = Color(nombre=f"Azul-{sufijo}", is_active=True)
        self.ciudad = Ciudad(nombre=f"Ciudad {sufijo}", departamento="Depto", is_active=True)
        self.db.add_all(
            [self.proveedor, self.categoria, self.temporada, self.talla_m, self.talla_l, self.color, self.ciudad]
        )
        self.db.commit()

        self.coleccion = Coleccion(nombre=f"Coleccion {sufijo}", temporada_id=self.temporada.id, is_active=True)
        self.sucursal_full = Sucursal(
            nombre=f"Sucursal Full {sufijo}",
            ciudad_id=self.ciudad.id,
            direccion="Av. Uno 100",
            telefono="70022222",
            is_active=True,
        )
        self.sucursal_parcial = Sucursal(
            nombre=f"Sucursal Parcial {sufijo}",
            ciudad_id=self.ciudad.id,
            direccion="Av. Dos 200",
            telefono="70033333",
            is_active=True,
        )
        self.db.add_all([self.coleccion, self.sucursal_full, self.sucursal_parcial])
        self.db.commit()

        self.producto = Producto(
            nombre=f"Chompa Andina {sufijo}",
            proveedor_id=self.proveedor.id,
            categoria_id=self.categoria.id,
            temporada_id=self.temporada.id,
            coleccion_id=self.coleccion.id,
            precio_venta=Decimal("100.00"),
            is_active=True,
            tallas=[self.talla_m, self.talla_l],
            colores=[self.color],
        )
        self.db.add(self.producto)
        self.db.commit()
        self.db.refresh(self.producto)

        self.variante_m = ProductoVariante(
            producto_id=self.producto.id, talla_id=self.talla_m.id, color_id=self.color.id, is_active=True
        )
        self.variante_l = ProductoVariante(
            producto_id=self.producto.id, talla_id=self.talla_l.id, color_id=self.color.id, is_active=True
        )
        self.db.add_all([self.variante_m, self.variante_l])
        self.db.commit()
        self.db.refresh(self.variante_m)
        self.db.refresh(self.variante_l)

        # sucursal_full: cubre ambas variantes.
        self.db.add_all(
            [
                StockSucursal(sucursal_id=self.sucursal_full.id, producto_variante_id=self.variante_m.id, cantidad=5),
                StockSucursal(sucursal_id=self.sucursal_full.id, producto_variante_id=self.variante_l.id, cantidad=5),
                # sucursal_parcial: solo tiene la M -- no cubre la compra completa.
                StockSucursal(
                    sucursal_id=self.sucursal_parcial.id, producto_variante_id=self.variante_m.id, cantidad=5
                ),
            ]
        )
        self.db.commit()

        self.cliente = _create_test_user(RolUsuario.CLIENTE)

        # Carrito armado vía los endpoints REALES de CU21 -- no se inserta a
        # mano, para que este test dependa del contrato público, no de la
        # tabla interna.
        r1 = client.post(
            "/api/v1/carrito/items", headers=self.headers(), json={"producto_variante_id": self.variante_m.id}
        )
        self.item_m_id = r1.json()["items"][0]["item_id"]
        r2 = client.post(
            "/api/v1/carrito/items", headers=self.headers(), json={"producto_variante_id": self.variante_l.id}
        )
        self.item_l_id = next(
            i["item_id"] for i in r2.json()["items"] if i["producto_variante_id"] == self.variante_l.id
        )
        # Segunda unidad de la variante M, pero DESELECCIONADA -- nunca debe
        # entrar a la compra.
        r3 = client.post(
            "/api/v1/carrito/items", headers=self.headers(), json={"producto_variante_id": self.variante_m.id}
        )
        self.item_m_no_elegido_id = next(
            i["item_id"]
            for i in r3.json()["items"]
            if i["producto_variante_id"] == self.variante_m.id and i["item_id"] not in (self.item_m_id,)
        )
        client.patch(
            f"/api/v1/carrito/items/{self.item_m_no_elegido_id}",
            headers=self.headers(),
            json={"seleccionado": False},
        )

    def headers(self) -> dict:
        return _auth_headers(self.cliente)

    def set_precio(self, precio: Decimal) -> None:
        producto = self.db.get(Producto, self.producto.id)
        producto.precio_venta = precio
        self.db.commit()

    def stock_actual(self, sucursal_id: int, variante_id: int) -> int:
        db = SessionLocal()
        try:
            fila = (
                db.query(StockSucursal)
                .filter(StockSucursal.sucursal_id == sucursal_id, StockSucursal.producto_variante_id == variante_id)
                .first()
            )
            return fila.cantidad if fila else 0
        finally:
            db.close()

    def stock_reservado(self, sucursal_id: int, variante_id: int) -> int:
        db = SessionLocal()
        try:
            fila = (
                db.query(StockSucursal)
                .filter(StockSucursal.sucursal_id == sucursal_id, StockSucursal.producto_variante_id == variante_id)
                .first()
            )
            return fila.stock_reservado if fila else 0
        finally:
            db.close()

    def carrito_item_ids(self) -> set[int]:
        respuesta = client.get("/api/v1/carrito", headers=self.headers())
        return {item["item_id"] for item in respuesta.json()["items"]}

    def cleanup(self) -> None:
        try:
            variante_ids = [self.variante_m.id, self.variante_l.id]
            self.db.query(VentaDetalle).filter(VentaDetalle.producto_variante_id.in_(variante_ids)).delete(
                synchronize_session=False
            )
            self.db.commit()
            ventas = self.db.query(Venta).filter(Venta.cliente_id == self.cliente.id).all()
            for venta in ventas:
                self.db.delete(venta)
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
            for variante in (self.variante_m, self.variante_l):
                obj = self.db.get(ProductoVariante, variante.id)
                if obj is not None:
                    self.db.delete(obj)
            self.db.commit()
            self.db.delete(self.producto)
            self.db.commit()
            self.db.delete(self.sucursal_full)
            self.db.delete(self.sucursal_parcial)
            self.db.delete(self.coleccion)
            self.db.delete(self.temporada)
            self.db.delete(self.categoria)
            self.db.delete(self.talla_m)
            self.db.delete(self.talla_l)
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


def test_resumen_sin_token_es_rechazado():
    response = client.get("/api/v1/compra-digital/resumen")
    assert response.status_code == 401


def test_confirmar_sin_token_es_rechazado():
    response = client.post("/api/v1/compra-digital", json={"sucursal_id": 1})
    assert response.status_code == 401


# --------------------------------------------------------------------------
# 1/2. CU22 recibe SOLO los items seleccionados -- los no seleccionados
# nunca entran a la compra.
# --------------------------------------------------------------------------


def test_resumen_incluye_solo_items_seleccionados():
    escenario = _EscenarioCompra()
    try:
        response = client.get("/api/v1/compra-digital/resumen", headers=escenario.headers())
        assert response.status_code == 200
        body = response.json()
        item_ids = {item["item_id"] for item in body["items"]}
        assert item_ids == {escenario.item_m_id, escenario.item_l_id}
        assert escenario.item_m_no_elegido_id not in item_ids
        assert Decimal(str(body["total"])) == Decimal("200.00")
    finally:
        escenario.cleanup()


def test_sin_ninguna_prenda_seleccionada_resumen_es_rechazado():
    escenario = _EscenarioCompra()
    try:
        # Deselecciona TODO.
        client.patch(
            f"/api/v1/carrito/items/{escenario.item_m_id}", headers=escenario.headers(), json={"seleccionado": False}
        )
        client.patch(
            f"/api/v1/carrito/items/{escenario.item_l_id}", headers=escenario.headers(), json={"seleccionado": False}
        )
        response = client.get("/api/v1/compra-digital/resumen", headers=escenario.headers())
        assert response.status_code == 422
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 4/5. Sucursal sin stock suficiente no puede seleccionarse; sucursal válida
# permite continuar.
# --------------------------------------------------------------------------


def test_sucursal_parcial_aparece_no_disponible_y_la_completa_si():
    escenario = _EscenarioCompra()
    try:
        response = client.get(
            "/api/v1/compra-digital/sucursales",
            params={"ciudad_id": escenario.ciudad.id},
            headers=escenario.headers(),
        )
        assert response.status_code == 200
        por_id = {s["id"]: s for s in response.json()}
        assert por_id[escenario.sucursal_full.id]["disponible_para_compra"] is True
        assert por_id[escenario.sucursal_parcial.id]["disponible_para_compra"] is False
    finally:
        escenario.cleanup()


def test_confirmar_con_sucursal_sin_disponibilidad_total_es_rechazado():
    escenario = _EscenarioCompra()
    try:
        response = client.post(
            "/api/v1/compra-digital",
            headers=escenario.headers(),
            json={"sucursal_id": escenario.sucursal_parcial.id},
        )
        assert response.status_code == 422
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 3/7/8. Una sola sucursal para toda la compra; código VT único; PENDIENTE_PAGO.
# --------------------------------------------------------------------------


def test_confirmar_con_sucursal_valida_crea_la_venta():
    escenario = _EscenarioCompra()
    try:
        response = client.post(
            "/api/v1/compra-digital",
            headers=escenario.headers(),
            json={"sucursal_id": escenario.sucursal_full.id},
        )
        assert response.status_code == 201
        body = response.json()
        assert re.fullmatch(r"VT-\d{5}", body["codigo_venta"])
        assert body["estado"] == "PENDIENTE_PAGO"
        assert body["tipo"] == "DIGITAL"
        assert body["sucursal"]["id"] == escenario.sucursal_full.id
        assert len(body["detalles"]) == 2
        assert Decimal(str(body["total"])) == Decimal("200.00")
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 6/9. FastAPI recalcula precio y total al confirmar; el detalle conserva el
# precio histórico aunque el producto cambie de precio DESPUÉS.
# --------------------------------------------------------------------------


def test_confirmar_recalcula_precio_y_total_y_conserva_precio_historico():
    escenario = _EscenarioCompra()
    try:
        # El resumen se armó con Bs 100 c/u -- se sube el precio ANTES de
        # confirmar: el total confirmado debe reflejar el precio NUEVO, no
        # el que el Cliente vio en la pantalla de resumen.
        escenario.set_precio(Decimal("150.00"))

        response = client.post(
            "/api/v1/compra-digital",
            headers=escenario.headers(),
            json={"sucursal_id": escenario.sucursal_full.id},
        )
        assert response.status_code == 201
        body = response.json()
        assert Decimal(str(body["total"])) == Decimal("300.00")
        for detalle in body["detalles"]:
            assert Decimal(str(detalle["precio_unitario"])) == Decimal("150.00")

        # Ahora sube el precio DE NUEVO, después de confirmada la compra --
        # el detalle ya creado debe conservar Bs 150, no el precio actual.
        escenario.set_precio(Decimal("999.00"))
        db = SessionLocal()
        try:
            venta = db.query(Venta).filter(Venta.codigo_venta == body["codigo_venta"]).one()
            for detalle in venta.detalles:
                assert detalle.precio_unitario == Decimal("150.00")
        finally:
            db.close()
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 10/11. CU22 no modifica stock ni elimina items del carrito.
# --------------------------------------------------------------------------


def test_confirmar_no_modifica_stock():
    escenario = _EscenarioCompra()
    try:
        client.post(
            "/api/v1/compra-digital",
            headers=escenario.headers(),
            json={"sucursal_id": escenario.sucursal_full.id},
        )
        assert escenario.stock_actual(escenario.sucursal_full.id, escenario.variante_m.id) == 5
        assert escenario.stock_reservado(escenario.sucursal_full.id, escenario.variante_m.id) == 0
        assert escenario.stock_actual(escenario.sucursal_full.id, escenario.variante_l.id) == 5
        assert escenario.stock_reservado(escenario.sucursal_full.id, escenario.variante_l.id) == 0
    finally:
        escenario.cleanup()


def test_confirmar_no_elimina_items_del_carrito():
    escenario = _EscenarioCompra()
    try:
        ids_antes = escenario.carrito_item_ids()
        client.post(
            "/api/v1/compra-digital",
            headers=escenario.headers(),
            json={"sucursal_id": escenario.sucursal_full.id},
        )
        ids_despues = escenario.carrito_item_ids()
        assert ids_despues == ids_antes
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 12. Un cliente nunca puede usar el carrito de otro.
# --------------------------------------------------------------------------


def test_cliente_no_puede_usar_items_del_carrito_de_otro():
    escenario_a = _EscenarioCompra()
    cliente_b = _create_test_user(RolUsuario.CLIENTE)
    try:
        # El cliente B no tiene nada seleccionado (ni carrito siquiera) --
        # no existe ningún parámetro con el que pueda referenciar los items
        # del cliente A: su propio resumen debe rechazarse por "sin selección".
        response = client.get("/api/v1/compra-digital/resumen", headers=_auth_headers(cliente_b))
        assert response.status_code == 422

        # Ni intentando confirmar contra la sucursal de A obtiene sus items.
        confirmar = client.post(
            "/api/v1/compra-digital",
            headers=_auth_headers(cliente_b),
            json={"sucursal_id": escenario_a.sucursal_full.id},
        )
        assert confirmar.status_code == 422
    finally:
        _delete_test_user(cliente_b.id)
        escenario_a.cleanup()
