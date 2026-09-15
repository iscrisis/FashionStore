"""Pruebas de CU12 - Consultar disponibilidad por sucursal (público, sin login).

Arma el escenario a mano (producto -> variantes -> stock por sucursal) igual
que test_consultar_catalogo_prendas.py para CU11: bypassa los endpoints
administrativos de CU08/CU06/CU14_ConsultarInventario y construye directamente
las mismas entidades que ellos ya administran, sin duplicar su lógica.
"""

import uuid
from datetime import date
from decimal import Decimal

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

client = TestClient(app)


class _DisponibilidadDePrueba:
    """Producto con 2 tallas x 2 colores (4 variantes) y 2 sucursales en
    ciudades distintas, con stock real en StockSucursal para algunas
    variantes -- el resto queda en 0 (agotado), tal como lo dejaría el
    Encargado (CU14_ConsultarInventario) sin tocar ese caso de uso aquí."""

    def __init__(self, *, producto_activo: bool = True, variante_activa: bool = True):
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
        self.ciudad_a = Ciudad(nombre=f"Ciudad A {sufijo}", departamento="Depto", is_active=True)
        self.ciudad_b = Ciudad(nombre=f"Ciudad B {sufijo}", departamento="Depto", is_active=True)
        self.db.add_all(
            [
                self.proveedor,
                self.categoria,
                self.temporada,
                self.talla_m,
                self.talla_l,
                self.color_rojo,
                self.color_negro,
                self.ciudad_a,
                self.ciudad_b,
            ]
        )
        self.db.commit()

        self.coleccion = Coleccion(
            nombre=f"Coleccion {sufijo}", temporada_id=self.temporada.id, is_active=True
        )
        self.sucursal_a = Sucursal(
            nombre=f"Sucursal A {sufijo}",
            ciudad_id=self.ciudad_a.id,
            direccion="Av. Siempre Viva 123",
            telefono="70022222",
            is_active=True,
        )
        self.sucursal_b = Sucursal(
            nombre=f"Sucursal B {sufijo}",
            ciudad_id=self.ciudad_b.id,
            direccion="Calle Falsa 456",
            telefono="70033333",
            is_active=True,
        )
        self.db.add_all([self.coleccion, self.sucursal_a, self.sucursal_b])
        self.db.commit()

        self.producto = Producto(
            nombre=f"Producto Disponibilidad {sufijo}",
            proveedor_id=self.proveedor.id,
            categoria_id=self.categoria.id,
            temporada_id=self.temporada.id,
            coleccion_id=self.coleccion.id,
            precio_venta=Decimal("149.90"),
            is_active=producto_activo,
            tallas=[self.talla_m, self.talla_l],
            colores=[self.color_rojo, self.color_negro],
        )
        self.db.add(self.producto)
        self.db.commit()
        self.db.refresh(self.producto)

        self.variante_rojo_m = ProductoVariante(
            producto_id=self.producto.id,
            talla_id=self.talla_m.id,
            color_id=self.color_rojo.id,
            is_active=variante_activa,
        )
        self.variante_rojo_l = ProductoVariante(
            producto_id=self.producto.id,
            talla_id=self.talla_l.id,
            color_id=self.color_rojo.id,
            is_active=True,
        )
        self.variante_negro_m = ProductoVariante(
            producto_id=self.producto.id,
            talla_id=self.talla_m.id,
            color_id=self.color_negro.id,
            is_active=True,
        )
        self.db.add_all(
            [self.variante_rojo_m, self.variante_rojo_l, self.variante_negro_m]
        )
        self.db.commit()

        # Stock real: Rojo/M tiene existencias en ambas sucursales, Rojo/L
        # solo en la sucursal A, Negro/M queda sin fila -- por eso el
        # servicio debe responder 0, no fallar.
        self.db.add_all(
            [
                StockSucursal(
                    sucursal_id=self.sucursal_a.id,
                    producto_variante_id=self.variante_rojo_m.id,
                    cantidad=5,
                ),
                StockSucursal(
                    sucursal_id=self.sucursal_b.id,
                    producto_variante_id=self.variante_rojo_m.id,
                    cantidad=2,
                ),
                StockSucursal(
                    sucursal_id=self.sucursal_a.id,
                    producto_variante_id=self.variante_rojo_l.id,
                    cantidad=3,
                ),
            ]
        )
        self.db.commit()

    def cleanup(self) -> None:
        try:
            self.db.query(StockSucursal).filter(
                StockSucursal.producto_variante_id.in_(
                    [self.variante_rojo_m.id, self.variante_rojo_l.id, self.variante_negro_m.id]
                )
            ).delete(synchronize_session=False)
            self.db.commit()
            self.db.delete(self.producto)
            self.db.commit()
            self.db.delete(self.sucursal_a)
            self.db.delete(self.sucursal_b)
            self.db.delete(self.coleccion)
            self.db.delete(self.temporada)
            self.db.delete(self.categoria)
            self.db.delete(self.talla_m)
            self.db.delete(self.talla_l)
            self.db.delete(self.color_rojo)
            self.db.delete(self.color_negro)
            self.db.delete(self.proveedor)
            self.db.commit()
            self.db.delete(self.ciudad_a)
            self.db.delete(self.ciudad_b)
            self.db.commit()
        finally:
            self.db.close()


def test_consultar_disponibilidad_no_requiere_login():
    escenario = _DisponibilidadDePrueba()
    try:
        response = client.get(
            "/api/v1/disponibilidad", params={"producto_id": escenario.producto.id}
        )
        assert response.status_code == 200
    finally:
        escenario.cleanup()


def test_disponibilidad_agrupa_por_sucursal_con_todas_las_variantes():
    escenario = _DisponibilidadDePrueba()
    try:
        response = client.get(
            "/api/v1/disponibilidad", params={"producto_id": escenario.producto.id}
        )
        body = response.json()
        assert body["producto_id"] == escenario.producto.id

        sucursales = {fila["sucursal_id"]: fila for fila in body["disponibilidad"]}
        # No se asume que sean las únicas sucursales activas -- el entorno
        # puede tener otras reales; solo importa que las de este escenario
        # aparezcan con los datos correctos.
        assert {escenario.sucursal_a.id, escenario.sucursal_b.id}.issubset(sucursales)

        # Las 3 variantes activas del producto aparecen en cada sucursal,
        # tenga o no stock cargado ahí -- el cliente necesita ver también lo
        # agotado, no solo lo disponible.
        variantes_a = {
            (v["color"], v["talla"]): v["cantidad"] for v in sucursales[escenario.sucursal_a.id]["variantes"]
        }
        assert variantes_a[(escenario.color_rojo.nombre, escenario.talla_m.nombre)] == 5
        assert variantes_a[(escenario.color_rojo.nombre, escenario.talla_l.nombre)] == 3
        assert variantes_a[(escenario.color_negro.nombre, escenario.talla_m.nombre)] == 0

        variantes_b = {
            (v["color"], v["talla"]): v["cantidad"] for v in sucursales[escenario.sucursal_b.id]["variantes"]
        }
        assert variantes_b[(escenario.color_rojo.nombre, escenario.talla_m.nombre)] == 2
        # Sin fila de stock para Rojo/L en la sucursal B -- debe responder 0, no omitirla.
        assert variantes_b[(escenario.color_rojo.nombre, escenario.talla_l.nombre)] == 0
    finally:
        escenario.cleanup()


def test_disponibilidad_filtra_por_ciudad():
    escenario = _DisponibilidadDePrueba()
    try:
        response = client.get(
            "/api/v1/disponibilidad",
            params={"producto_id": escenario.producto.id, "ciudad_id": escenario.ciudad_a.id},
        )
        sucursales_ids = {fila["sucursal_id"] for fila in response.json()["disponibilidad"]}
        assert sucursales_ids == {escenario.sucursal_a.id}
    finally:
        escenario.cleanup()


def test_disponibilidad_variante_inactiva_no_aparece():
    escenario = _DisponibilidadDePrueba(variante_activa=False)
    try:
        response = client.get(
            "/api/v1/disponibilidad", params={"producto_id": escenario.producto.id}
        )
        primera_sucursal = response.json()["disponibilidad"][0]
        combinaciones = {(v["color"], v["talla"]) for v in primera_sucursal["variantes"]}
        assert (escenario.color_rojo.nombre, escenario.talla_m.nombre) not in combinaciones
    finally:
        escenario.cleanup()


def test_disponibilidad_producto_inactivo_devuelve_404():
    escenario = _DisponibilidadDePrueba(producto_activo=False)
    try:
        response = client.get(
            "/api/v1/disponibilidad", params={"producto_id": escenario.producto.id}
        )
        assert response.status_code == 404
    finally:
        escenario.cleanup()


def test_disponibilidad_producto_inexistente_devuelve_404():
    response = client.get("/api/v1/disponibilidad", params={"producto_id": 9999999})
    assert response.status_code == 404


def test_disponibilidad_requiere_producto_id():
    response = client.get("/api/v1/disponibilidad")
    assert response.status_code == 422
