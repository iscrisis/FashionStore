"""Pruebas de CU21 -- Usar carrito de compras (Cliente).

Arma el escenario a mano (producto -> 2 tallas x 2 colores -> 3 variantes con
stock en una sucursal, más una segunda sucursal para el caso "ninguna
sucursal cubre la cantidad") -- mismo patrón ya usado por
test_crear_reserva_prendas.py, sin reconstruir su lógica de fecha/hora (CU21
no la necesita).

Corrección: cada CarritoItem es UNA unidad concreta de una variante -- ya NO
existe `cantidad`. Agregar la MISMA variante dos veces crea DOS items
independientes (dos unidades), cada uno con su propio `seleccionado`. Énfasis
en: el carrito es SOLO intención de compra digital (nunca toca
StockSucursal.cantidad ni .stock_reservado), un Cliente jamás ve ni modifica
el carrito de otro, y la disponibilidad se valida contra "al menos una
sucursal activa", no una en particular.
"""

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

client = TestClient(app)


class _EscenarioCarrito:
    """Un producto con 3 variantes (Rojo/M, Negro/M, Rojo/L), stock conocido
    en una sucursal activa, más un Cliente."""

    def __init__(self, *, stock_inicial: int = 5, stock_sucursal_b: int | None = None):
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
        self.color_rojo = Color(nombre=f"Rojo-{sufijo}", is_active=True)
        self.color_negro = Color(nombre=f"Negro-{sufijo}", is_active=True)
        self.ciudad = Ciudad(nombre=f"Ciudad {sufijo}", departamento="Depto", is_active=True)
        self.db.add_all(
            [
                self.proveedor,
                self.categoria,
                self.temporada,
                self.talla_m,
                self.talla_l,
                self.color_rojo,
                self.color_negro,
                self.ciudad,
            ]
        )
        self.db.commit()

        self.coleccion = Coleccion(
            nombre=f"Coleccion {sufijo}", temporada_id=self.temporada.id, is_active=True
        )
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
            nombre=f"Blusa Essential {sufijo}",
            proveedor_id=self.proveedor.id,
            categoria_id=self.categoria.id,
            temporada_id=self.temporada.id,
            coleccion_id=self.coleccion.id,
            precio_venta=Decimal("120.00"),
            is_active=True,
            tallas=[self.talla_m, self.talla_l],
            colores=[self.color_rojo, self.color_negro],
        )
        self.db.add(self.producto)
        self.db.commit()
        self.db.refresh(self.producto)

        self.variante_rojo_m = ProductoVariante(
            producto_id=self.producto.id, talla_id=self.talla_m.id, color_id=self.color_rojo.id, is_active=True
        )
        self.variante_negro_m = ProductoVariante(
            producto_id=self.producto.id, talla_id=self.talla_m.id, color_id=self.color_negro.id, is_active=True
        )
        self.variante_rojo_l = ProductoVariante(
            producto_id=self.producto.id, talla_id=self.talla_l.id, color_id=self.color_rojo.id, is_active=True
        )
        self.db.add_all([self.variante_rojo_m, self.variante_negro_m, self.variante_rojo_l])
        self.db.commit()
        for v in (self.variante_rojo_m, self.variante_negro_m, self.variante_rojo_l):
            self.db.refresh(v)

        for variante in (self.variante_rojo_m, self.variante_negro_m, self.variante_rojo_l):
            self.db.add(
                StockSucursal(sucursal_id=self.sucursal.id, producto_variante_id=variante.id, cantidad=stock_inicial)
            )
        self.db.commit()

        self.sucursal_b = None
        if stock_sucursal_b is not None:
            self.sucursal_b = Sucursal(
                nombre=f"Sucursal B {sufijo}",
                ciudad_id=self.ciudad.id,
                direccion="Otra Av. 456",
                telefono="70033333",
                is_active=True,
            )
            self.db.add(self.sucursal_b)
            self.db.commit()
            self.db.add(
                StockSucursal(
                    sucursal_id=self.sucursal_b.id,
                    producto_variante_id=self.variante_rojo_m.id,
                    cantidad=stock_sucursal_b,
                )
            )
            self.db.commit()

        self.cliente = _create_test_user(RolUsuario.CLIENTE)

    def headers(self) -> dict:
        return _auth_headers(self.cliente)

    def _fila_stock(self, variante_id: int, sucursal_id: int | None = None) -> StockSucursal | None:
        db = SessionLocal()
        try:
            return (
                db.query(StockSucursal)
                .filter(
                    StockSucursal.sucursal_id == (sucursal_id or self.sucursal.id),
                    StockSucursal.producto_variante_id == variante_id,
                )
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

    def agregar(self, variante_id: int) -> dict:
        response = client.post(
            "/api/v1/carrito/items",
            headers=self.headers(),
            json={"producto_variante_id": variante_id},
        )
        return response

    def cleanup(self) -> None:
        try:
            variante_ids = [self.variante_rojo_m.id, self.variante_negro_m.id, self.variante_rojo_l.id]
            self.db.query(CarritoItem).filter(CarritoItem.producto_variante_id.in_(variante_ids)).delete(
                synchronize_session=False
            )
            self.db.commit()
            self.db.query(Carrito).filter(Carrito.cliente_id == self.cliente.id).delete(
                synchronize_session=False
            )
            self.db.commit()
            _delete_test_user(self.cliente.id)
            self.db.query(StockSucursal).filter(StockSucursal.producto_variante_id.in_(variante_ids)).delete(
                synchronize_session=False
            )
            self.db.commit()
            for variante in (self.variante_rojo_m, self.variante_negro_m, self.variante_rojo_l):
                obj = self.db.get(ProductoVariante, variante.id)
                if obj is not None:
                    self.db.delete(obj)
            self.db.commit()
            self.db.delete(self.producto)
            self.db.commit()
            if self.sucursal_b is not None:
                self.db.delete(self.sucursal_b)
            self.db.delete(self.sucursal)
            self.db.delete(self.coleccion)
            self.db.delete(self.temporada)
            self.db.delete(self.categoria)
            self.db.delete(self.talla_m)
            self.db.delete(self.talla_l)
            self.db.delete(self.color_rojo)
            self.db.delete(self.color_negro)
            self.db.delete(self.proveedor)
            self.db.commit()
            self.db.delete(self.ciudad)
            self.db.commit()
        finally:
            self.db.close()


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_consultar_carrito_sin_token_es_rechazado():
    response = client.get("/api/v1/carrito")
    assert response.status_code == 401


def test_agregar_sin_token_es_rechazado():
    response = client.post("/api/v1/carrito/items", json={"producto_variante_id": 1})
    assert response.status_code == 401


def test_otro_rol_no_puede_usar_el_carrito():
    escenario = _EscenarioCarrito()
    encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal.id)
    try:
        response = client.get("/api/v1/carrito", headers=_auth_headers(encargado))
        assert response.status_code == 403
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_carrito_vacio_al_inicio():
    escenario = _EscenarioCarrito()
    try:
        response = client.get("/api/v1/carrito", headers=escenario.headers())
        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert Decimal(body["subtotal_seleccionado"]) == Decimal("0")
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 1. Agregar una variante crea una unidad.
# --------------------------------------------------------------------------


def test_agregar_una_variante_crea_una_unidad():
    escenario = _EscenarioCarrito()
    try:
        response = escenario.agregar(escenario.variante_rojo_m.id)
        assert response.status_code == 201
        body = response.json()
        assert len(body["items"]) == 1
        item = body["items"][0]
        assert item["producto_variante_id"] == escenario.variante_rojo_m.id
        assert item["producto"]["nombre"] == escenario.producto.nombre
        assert item["variante"]["color"]["nombre"] == escenario.color_rojo.nombre
        assert item["variante"]["talla"]["nombre"] == escenario.talla_m.nombre
        assert Decimal(item["precio_unitario"]) == Decimal("120.00")
        assert item["seleccionado"] is True
        assert Decimal(body["subtotal_seleccionado"]) == Decimal("120.00")
        assert "cantidad" not in item
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 2. Agregar otra variante crea otro item.
# --------------------------------------------------------------------------


def test_agregar_otra_variante_crea_otro_item():
    escenario = _EscenarioCarrito()
    try:
        escenario.agregar(escenario.variante_rojo_m.id)
        response = escenario.agregar(escenario.variante_negro_m.id)
        assert response.status_code == 201
        items = response.json()["items"]
        assert len(items) == 2
        item_ids = {item["item_id"] for item in items}
        assert len(item_ids) == 2
        variantes = {item["producto_variante_id"] for item in items}
        assert variantes == {escenario.variante_rojo_m.id, escenario.variante_negro_m.id}
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 3. Agregar dos veces la misma variante permite dos unidades individuales
#    (nunca fusiona/incrementa, nunca falla por duplicado).
# --------------------------------------------------------------------------


def test_agregar_dos_veces_la_misma_variante_crea_dos_unidades_independientes():
    escenario = _EscenarioCarrito()
    try:
        primero = escenario.agregar(escenario.variante_rojo_m.id)
        segundo = escenario.agregar(escenario.variante_rojo_m.id)
        assert primero.status_code == 201
        assert segundo.status_code == 201

        items = segundo.json()["items"]
        assert len(items) == 2
        assert all(item["producto_variante_id"] == escenario.variante_rojo_m.id for item in items)
        item_ids = {item["item_id"] for item in items}
        assert len(item_ids) == 2  # dos filas distintas, no una con cantidad=2
        assert Decimal(segundo.json()["subtotal_seleccionado"]) == Decimal("240.00")
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 4. Se puede seleccionar una unidad sin seleccionar la otra.
# --------------------------------------------------------------------------


def test_seleccionar_una_unidad_sin_seleccionar_la_otra():
    escenario = _EscenarioCarrito()
    try:
        escenario.agregar(escenario.variante_rojo_m.id)
        creado = escenario.agregar(escenario.variante_negro_m.id)
        items = creado.json()["items"]
        item_rojo = next(i for i in items if i["producto_variante_id"] == escenario.variante_rojo_m.id)
        item_negro = next(i for i in items if i["producto_variante_id"] == escenario.variante_negro_m.id)

        response = client.patch(
            f"/api/v1/carrito/items/{item_negro['item_id']}",
            headers=escenario.headers(),
            json={"seleccionado": False},
        )
        assert response.status_code == 200
        actualizado = {item["item_id"]: item for item in response.json()["items"]}
        assert actualizado[item_rojo["item_id"]]["seleccionado"] is True
        assert actualizado[item_negro["item_id"]]["seleccionado"] is False
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 5. Eliminar una unidad no elimina la otra (misma variante, dos unidades).
# --------------------------------------------------------------------------


def test_eliminar_una_unidad_no_elimina_la_otra():
    escenario = _EscenarioCarrito()
    try:
        escenario.agregar(escenario.variante_rojo_m.id)
        creado = escenario.agregar(escenario.variante_rojo_m.id)
        items = creado.json()["items"]
        assert len(items) == 2
        a_eliminar, sobreviviente = items[0], items[1]

        response = client.delete(
            f"/api/v1/carrito/items/{a_eliminar['item_id']}", headers=escenario.headers()
        )
        assert response.status_code == 200
        restantes = response.json()["items"]
        assert len(restantes) == 1
        assert restantes[0]["item_id"] == sobreviviente["item_id"]

        confirmacion = client.get("/api/v1/carrito", headers=escenario.headers()).json()
        assert len(confirmacion["items"]) == 1
        assert confirmacion["items"][0]["item_id"] == sobreviviente["item_id"]
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 6. El subtotal refleja SOLO lo seleccionado.
# --------------------------------------------------------------------------


def test_subtotal_seleccionado_refleja_solo_lo_seleccionado():
    escenario = _EscenarioCarrito()
    try:
        escenario.agregar(escenario.variante_rojo_m.id)
        creado = escenario.agregar(escenario.variante_negro_m.id)
        items = creado.json()["items"]
        item_a_deseleccionar = items[0]

        response = client.patch(
            f"/api/v1/carrito/items/{item_a_deseleccionar['item_id']}",
            headers=escenario.headers(),
            json={"seleccionado": False},
        )
        assert Decimal(response.json()["subtotal_seleccionado"]) == Decimal("120.00")

        # Deseleccionar también la otra -> subtotal en 0 (el frontend muestra
        # el mensaje "Selecciona al menos una prenda para continuar.").
        item_restante = next(
            i for i in response.json()["items"] if i["item_id"] != item_a_deseleccionar["item_id"]
        )
        final = client.patch(
            f"/api/v1/carrito/items/{item_restante['item_id']}",
            headers=escenario.headers(),
            json={"seleccionado": False},
        )
        assert Decimal(final.json()["subtotal_seleccionado"]) == Decimal("0")
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# 7. Agregar al carrito NO cambia stock_actual ni stock_reservado -- ni
#    siquiera agregando varias unidades de la misma variante.
# --------------------------------------------------------------------------


def test_agregar_al_carrito_no_cambia_stock():
    escenario = _EscenarioCarrito(stock_inicial=5)
    try:
        escenario.agregar(escenario.variante_rojo_m.id)
        escenario.agregar(escenario.variante_rojo_m.id)
        assert escenario.stock_actual(escenario.variante_rojo_m.id) == 5
        assert escenario.stock_reservado(escenario.variante_rojo_m.id) == 0
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Disponibilidad: una unidad más de la que ninguna sucursal puede cubrir se
# rechaza; la que sí es cubierta por al menos una sucursal se acepta.
# --------------------------------------------------------------------------


def test_unidad_que_ninguna_sucursal_cubre_es_rechazada():
    escenario = _EscenarioCarrito(stock_inicial=1, stock_sucursal_b=1)
    try:
        escenario.agregar(escenario.variante_rojo_m.id)  # 1ra unidad: OK (sucursal A cubre 1)
        segunda = escenario.agregar(escenario.variante_rojo_m.id)  # 2da: ninguna sucursal tiene 2
        assert segunda.status_code == 422

        confirmacion = client.get("/api/v1/carrito", headers=escenario.headers()).json()
        assert len(confirmacion["items"]) == 1
    finally:
        escenario.cleanup()


def test_unidad_cubierta_por_al_menos_una_sucursal_es_aceptada():
    # Sucursal A tiene 1, sucursal B tiene 3 -- la 2da unidad solo la cubre B.
    escenario = _EscenarioCarrito(stock_inicial=1, stock_sucursal_b=3)
    try:
        escenario.agregar(escenario.variante_rojo_m.id)
        segunda = escenario.agregar(escenario.variante_rojo_m.id)
        assert segunda.status_code == 201
        assert len(segunda.json()["items"]) == 2
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Aislamiento entre clientes.
# --------------------------------------------------------------------------


def test_consultar_carrito_devuelve_solo_el_del_cliente():
    escenario_a = _EscenarioCarrito()
    escenario_b = _EscenarioCarrito()
    try:
        escenario_a.agregar(escenario_a.variante_rojo_m.id)
        respuesta_b = client.get("/api/v1/carrito", headers=escenario_b.headers())
        assert respuesta_b.status_code == 200
        assert respuesta_b.json()["items"] == []
    finally:
        escenario_a.cleanup()
        escenario_b.cleanup()


def test_otro_cliente_no_puede_seleccionar_un_item_ajeno():
    escenario_a = _EscenarioCarrito()
    escenario_b = _EscenarioCarrito()
    try:
        creado = escenario_a.agregar(escenario_a.variante_rojo_m.id)
        item_id = creado.json()["items"][0]["item_id"]

        response = client.patch(
            f"/api/v1/carrito/items/{item_id}", headers=escenario_b.headers(), json={"seleccionado": False}
        )
        assert response.status_code == 404

        propio = client.get("/api/v1/carrito", headers=escenario_a.headers()).json()
        assert propio["items"][0]["seleccionado"] is True
    finally:
        escenario_a.cleanup()
        escenario_b.cleanup()


def test_otro_cliente_no_puede_eliminar_un_item_ajeno():
    escenario_a = _EscenarioCarrito()
    escenario_b = _EscenarioCarrito()
    try:
        creado = escenario_a.agregar(escenario_a.variante_rojo_m.id)
        item_id = creado.json()["items"][0]["item_id"]

        response = client.delete(f"/api/v1/carrito/items/{item_id}", headers=escenario_b.headers())
        assert response.status_code == 404

        propio = client.get("/api/v1/carrito", headers=escenario_a.headers()).json()
        assert len(propio["items"]) == 1
    finally:
        escenario_a.cleanup()
        escenario_b.cleanup()
