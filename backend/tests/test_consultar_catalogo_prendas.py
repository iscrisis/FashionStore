"""Pruebas de CU11 - Consultar catálogo de prendas (público, sin login)."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_imagen import ProductoImagen
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada

client = TestClient(app)


class _CatalogoDePrueba:
    """Crea (y limpia) un producto activo completo -- proveedor, categoría,
    temporada, colección, talla, color e imágenes -- para probar el catálogo
    público (CU11) sin depender de los endpoints administrativos de CU08."""

    def __init__(self, *, producto_activo: bool = True, categoria_activa: bool = True):
        self.db = SessionLocal()
        sufijo = uuid.uuid4().hex[:8]

        self.proveedor = Proveedor(
            razon_social=f"Proveedor {sufijo}",
            nombre_contacto="Ana",
            correo=f"ana-{sufijo}@textiles.com",
            telefono="70011111",
            is_active=True,
        )
        self.categoria = Categoria(nombre=f"Categoria {sufijo}", is_active=categoria_activa)
        self.temporada = Temporada(
            nombre=f"Temporada {sufijo}",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 3, 31),
            is_active=True,
        )
        self.talla = Talla(nombre=f"M-{sufijo}", is_active=True)
        self.color = Color(nombre=f"Negro-{sufijo}", is_active=True)
        self.db.add_all([self.proveedor, self.categoria, self.temporada, self.talla, self.color])
        self.db.commit()

        self.coleccion = Coleccion(
            nombre=f"Coleccion {sufijo}", temporada_id=self.temporada.id, is_active=True
        )
        self.db.add(self.coleccion)
        self.db.commit()

        self.producto = Producto(
            nombre=f"Producto Publico {sufijo}",
            descripcion="Prenda de prueba para el catálogo público",
            proveedor_id=self.proveedor.id,
            categoria_id=self.categoria.id,
            temporada_id=self.temporada.id,
            coleccion_id=self.coleccion.id,
            precio_venta=Decimal("199.90"),
            imagen_principal_url="/api/v1/media/productos/principal-fake.png",
            is_active=producto_activo,
            tallas=[self.talla],
            colores=[self.color],
        )
        self.producto.imagenes.append(
            ProductoImagen(url="/api/v1/media/productos/adicional-fake.png", orden=0)
        )
        self.db.add(self.producto)
        self.db.commit()
        self.db.refresh(self.producto)

    def cleanup(self) -> None:
        try:
            self.db.delete(self.producto)
            self.db.commit()
            self.db.delete(self.coleccion)
            self.db.delete(self.temporada)
            self.db.delete(self.categoria)
            self.db.delete(self.talla)
            self.db.delete(self.color)
            self.db.delete(self.proveedor)
            self.db.commit()
        finally:
            self.db.close()


# --------------------------------------------------------------------------
# Acceso público (sin token)
# --------------------------------------------------------------------------


def test_listar_categorias_no_requiere_login():
    response = client.get("/api/v1/catalogo/categorias")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_listar_productos_no_requiere_login():
    response = client.get("/api/v1/catalogo/productos")
    assert response.status_code == 200


def test_obtener_producto_no_requiere_login():
    catalogo = _CatalogoDePrueba()
    try:
        response = client.get(f"/api/v1/catalogo/productos/{catalogo.producto.id}")
        assert response.status_code == 200
    finally:
        catalogo.cleanup()


# --------------------------------------------------------------------------
# Estructura de datos públicos
# --------------------------------------------------------------------------


def test_producto_publico_incluye_precio_numerico_e_imagenes():
    catalogo = _CatalogoDePrueba()
    try:
        response = client.get(f"/api/v1/catalogo/productos/{catalogo.producto.id}")
        body = response.json()
        assert body["precio_venta"] == 199.90
        assert isinstance(body["precio_venta"], float)
        assert body["imagen_principal_url"] == "/api/v1/media/productos/principal-fake.png"
        assert body["imagenes"][0]["url"] == "/api/v1/media/productos/adicional-fake.png"
        assert body["categoria"]["nombre"] == catalogo.categoria.nombre
        assert body["temporada"]["nombre"] == catalogo.temporada.nombre
        assert body["coleccion"]["nombre"] == catalogo.coleccion.nombre
        assert body["tallas"][0]["nombre"] == catalogo.talla.nombre
        assert body["colores"][0]["nombre"] == catalogo.color.nombre
        # Sin campos administrativos: CU11 es una vista pública, no un espejo del admin.
        assert "proveedor_id" not in body
        assert "producto_proveedor_id" not in body
        assert "is_active" not in body
    finally:
        catalogo.cleanup()


def test_categoria_publica_incluye_imagen_url():
    catalogo = _CatalogoDePrueba()
    try:
        response = client.get("/api/v1/catalogo/categorias")
        categoria = next(c for c in response.json() if c["id"] == catalogo.categoria.id)
        assert "imagen_url" in categoria
    finally:
        catalogo.cleanup()


# --------------------------------------------------------------------------
# Solo información activa/publicable
# --------------------------------------------------------------------------


def test_producto_inactivo_no_aparece_en_el_catalogo():
    catalogo = _CatalogoDePrueba(producto_activo=False)
    try:
        listado = client.get("/api/v1/catalogo/productos")
        assert catalogo.producto.id not in {p["id"] for p in listado.json()}

        detalle = client.get(f"/api/v1/catalogo/productos/{catalogo.producto.id}")
        assert detalle.status_code == 404
    finally:
        catalogo.cleanup()


def test_categoria_inactiva_no_aparece_en_el_catalogo():
    catalogo = _CatalogoDePrueba(categoria_activa=False)
    try:
        listado = client.get("/api/v1/catalogo/categorias")
        assert catalogo.categoria.id not in {c["id"] for c in listado.json()}
    finally:
        catalogo.cleanup()


def test_obtener_producto_inexistente_devuelve_404():
    response = client.get("/api/v1/catalogo/productos/9999999")
    assert response.status_code == 404


# --------------------------------------------------------------------------
# Filtros
# --------------------------------------------------------------------------


def test_filtrar_productos_por_categoria_coleccion_talla_y_color():
    catalogo = _CatalogoDePrueba()
    try:
        por_categoria = client.get(f"/api/v1/catalogo/productos?categoria_id={catalogo.categoria.id}")
        assert catalogo.producto.id in {p["id"] for p in por_categoria.json()}

        por_coleccion = client.get(f"/api/v1/catalogo/productos?coleccion_id={catalogo.coleccion.id}")
        assert catalogo.producto.id in {p["id"] for p in por_coleccion.json()}

        por_talla = client.get(f"/api/v1/catalogo/productos?talla_id={catalogo.talla.id}")
        assert catalogo.producto.id in {p["id"] for p in por_talla.json()}

        por_color = client.get(f"/api/v1/catalogo/productos?color_id={catalogo.color.id}")
        assert catalogo.producto.id in {p["id"] for p in por_color.json()}

        por_busqueda = client.get(f"/api/v1/catalogo/productos?search={catalogo.producto.nombre[:10]}")
        assert catalogo.producto.id in {p["id"] for p in por_busqueda.json()}

        otra_categoria_id = catalogo.categoria.id + 1_000_000
        sin_match = client.get(f"/api/v1/catalogo/productos?categoria_id={otra_categoria_id}")
        assert catalogo.producto.id not in {p["id"] for p in sin_match.json()}
    finally:
        catalogo.cleanup()


def test_listar_colecciones_filtra_por_temporada():
    catalogo = _CatalogoDePrueba()
    try:
        response = client.get(f"/api/v1/catalogo/colecciones?temporada_id={catalogo.temporada.id}")
        assert catalogo.coleccion.id in {c["id"] for c in response.json()}
    finally:
        catalogo.cleanup()


def test_listar_tallas_y_colores_activos():
    catalogo = _CatalogoDePrueba()
    try:
        tallas = client.get("/api/v1/catalogo/tallas")
        assert catalogo.talla.id in {t["id"] for t in tallas.json()}

        colores = client.get("/api/v1/catalogo/colores")
        assert catalogo.color.id in {c["id"] for c in colores.json()}
    finally:
        catalogo.cleanup()
