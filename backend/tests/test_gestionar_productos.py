"""Pruebas de CU08 - Gestionar productos."""

import uuid
from datetime import date

from fastapi.testclient import TestClient

from app.core.image_storage import UPLOADS_ROOT, eliminar_archivo_imagen
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.categoria import Categoria
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.color import Color
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P1_SucursalesYCatalogos.Models.producto_proveedor import ProductoProveedor
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.talla import Talla
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

client = TestClient(app)


def _create_test_user(rol: RolUsuario) -> Usuario:
    db = SessionLocal()
    try:
        usuario = Usuario(
            nombre="Usuario de prueba",
            correo=f"test-{uuid.uuid4().hex[:10]}@fashionstore.com",
            password_hash=hash_password("ClaveSegura123!"),
            rol=rol,
            is_active=True,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario
    finally:
        db.close()


def _delete_test_user(usuario_id: int) -> None:
    db = SessionLocal()
    try:
        usuario = db.get(Usuario, usuario_id)
        if usuario is not None:
            db.delete(usuario)
            db.commit()
    finally:
        db.close()


def _auth_headers(usuario: Usuario) -> dict:
    token = create_access_token(subject=str(usuario.id), extra_claims={"rol": usuario.rol.value})
    return {"Authorization": f"Bearer {token}"}


class _Catalogo:
    """Crea (y limpia) todo el catálogo base que CU08 reutiliza: proveedor,
    categoría, temporada, colección, tallas y colores."""

    def __init__(self):
        self.db = SessionLocal()
        sufijo = uuid.uuid4().hex[:8]

        self.proveedor = Proveedor(
            razon_social=f"Proveedor {sufijo}",
            nombre_contacto="Juan Pérez",
            correo=f"proveedor-{sufijo}@textiles.com",
            telefono="70012345",
            is_active=True,
        )
        self.categoria = Categoria(nombre=f"Categoria {sufijo}", is_active=True)
        self.temporada = Temporada(
            nombre=f"Temporada {sufijo}",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 3, 31),
            is_active=True,
        )
        self.talla_s = Talla(nombre=f"S-{sufijo}", is_active=True)
        self.talla_m = Talla(nombre=f"M-{sufijo}", is_active=True)
        self.color_negro = Color(nombre=f"Negro-{sufijo}", is_active=True)
        self.color_blanco = Color(nombre=f"Blanco-{sufijo}", is_active=True)

        self.db.add_all(
            [
                self.proveedor,
                self.categoria,
                self.temporada,
                self.talla_s,
                self.talla_m,
                self.color_negro,
                self.color_blanco,
            ]
        )
        self.db.commit()

        self.coleccion = Coleccion(
            nombre=f"Coleccion {sufijo}", temporada_id=self.temporada.id, is_active=True
        )
        self.otra_temporada = Temporada(
            nombre=f"Otra temporada {sufijo}",
            fecha_inicio=date(2026, 6, 1),
            fecha_fin=date(2026, 8, 31),
            is_active=True,
        )
        self.db.add_all([self.coleccion, self.otra_temporada])
        self.db.commit()
        for obj in (
            self.proveedor,
            self.categoria,
            self.temporada,
            self.coleccion,
            self.otra_temporada,
            self.talla_s,
            self.talla_m,
            self.color_negro,
            self.color_blanco,
        ):
            self.db.refresh(obj)

    def payload(self, **overrides) -> dict:
        base = {
            "nombre": f"Producto {uuid.uuid4().hex[:8]}",
            "descripcion": "Prenda de prueba",
            "proveedor_id": self.proveedor.id,
            "categoria_id": self.categoria.id,
            "temporada_id": self.temporada.id,
            "coleccion_id": self.coleccion.id,
            "precio_venta": "399.00",
            "talla_ids": [self.talla_s.id, self.talla_m.id],
            "color_ids": [self.color_negro.id, self.color_blanco.id],
        }
        base.update(overrides)
        return base

    def crear_propuesta(self, *, disponibilidad: bool = True) -> ProductoProveedor:
        propuesta = ProductoProveedor(
            proveedor_id=self.proveedor.id,
            nombre=f"Propuesta {uuid.uuid4().hex[:8]}",
            descripcion="Prenda ofrecida por el proveedor",
            temporada_id=self.temporada.id,
            coleccion_id=self.coleccion.id,
            disponibilidad=disponibilidad,
            is_active=True,
        )
        self.db.add(propuesta)
        self.db.commit()
        self.db.refresh(propuesta)
        return propuesta

    def cleanup(self) -> None:
        try:
            for producto in self.db.query(Producto).filter(Producto.proveedor_id == self.proveedor.id):
                self.db.delete(producto)
            self.db.commit()

            for propuesta in (
                self.db.query(ProductoProveedor)
                .filter(ProductoProveedor.proveedor_id == self.proveedor.id)
                .all()
            ):
                self.db.delete(propuesta)
            self.db.commit()

            self.db.delete(self.coleccion)
            self.db.commit()
            self.db.delete(self.temporada)
            self.db.delete(self.otra_temporada)
            self.db.delete(self.categoria)
            self.db.delete(self.proveedor)
            self.db.delete(self.talla_s)
            self.db.delete(self.talla_m)
            self.db.delete(self.color_negro)
            self.db.delete(self.color_blanco)
            self.db.commit()
        finally:
            self.db.close()


def _delete_test_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        producto = db.get(Producto, producto_id)
        if producto is not None:
            db.delete(producto)
            db.commit()
    finally:
        db.close()


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_listar_productos_sin_token_es_rechazado():
    assert client.get("/api/v1/productos").status_code == 401


def test_listar_con_rol_no_autorizado_es_rechazado():
    cajero = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.get("/api/v1/productos", headers=_auth_headers(cajero))
        assert response.status_code == 403
    finally:
        _delete_test_user(cajero.id)


# --------------------------------------------------------------------------
# Registrar producto
# --------------------------------------------------------------------------


def test_crear_producto_ok_genera_variantes_talla_color():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    producto_id = None
    try:
        response = client.post(
            "/api/v1/productos", headers=_auth_headers(admin), json=catalogo.payload()
        )
        assert response.status_code == 201
        body = response.json()
        producto_id = body["id"]
        assert body["precio_venta"] == "399.00"
        assert body["is_active"] is True
        assert body["proveedor"]["id"] == catalogo.proveedor.id
        assert {t["id"] for t in body["tallas"]} == {catalogo.talla_s.id, catalogo.talla_m.id}
        assert {c["id"] for c in body["colores"]} == {catalogo.color_negro.id, catalogo.color_blanco.id}
        # 2 tallas x 2 colores = 4 variantes
        assert len(body["variantes"]) == 4
        combinaciones = {(v["talla"]["id"], v["color"]["id"]) for v in body["variantes"]}
        assert (catalogo.talla_s.id, catalogo.color_negro.id) in combinaciones
        assert (catalogo.talla_m.id, catalogo.color_blanco.id) in combinaciones
    finally:
        if producto_id:
            _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_crear_producto_con_precio_no_positivo_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    try:
        response = client.post(
            "/api/v1/productos",
            headers=_auth_headers(admin),
            json=catalogo.payload(precio_venta="0"),
        )
        assert response.status_code == 422
    finally:
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_crear_producto_sin_tallas_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    try:
        response = client.post(
            "/api/v1/productos", headers=_auth_headers(admin), json=catalogo.payload(talla_ids=[])
        )
        assert response.status_code == 422
    finally:
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_crear_producto_con_categoria_inexistente_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    try:
        response = client.post(
            "/api/v1/productos",
            headers=_auth_headers(admin),
            json=catalogo.payload(categoria_id=9_999_999),
        )
        assert response.status_code == 422
    finally:
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_crear_producto_con_coleccion_de_otra_temporada_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    try:
        response = client.post(
            "/api/v1/productos",
            headers=_auth_headers(admin),
            json=catalogo.payload(temporada_id=catalogo.otra_temporada.id),
        )
        assert response.status_code == 422
    finally:
        catalogo.cleanup()
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Reutilizar propuesta de proveedor
# --------------------------------------------------------------------------


def test_convertir_propuesta_en_producto_ok_y_desaparece_de_disponibles():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    propuesta = catalogo.crear_propuesta()
    producto_id = None
    try:
        disponibles_antes = client.get(
            "/api/v1/productos/propuestas", headers=_auth_headers(admin)
        ).json()
        assert propuesta.id in {p["id"] for p in disponibles_antes}

        response = client.post(
            "/api/v1/productos",
            headers=_auth_headers(admin),
            json=catalogo.payload(
                nombre=propuesta.nombre,
                descripcion=propuesta.descripcion,
                producto_proveedor_id=propuesta.id,
            ),
        )
        assert response.status_code == 201
        body = response.json()
        producto_id = body["id"]
        assert body["producto_proveedor_id"] == propuesta.id

        disponibles_despues = client.get(
            "/api/v1/productos/propuestas", headers=_auth_headers(admin)
        ).json()
        assert propuesta.id not in {p["id"] for p in disponibles_despues}
    finally:
        if producto_id:
            _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_convertir_la_misma_propuesta_dos_veces_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    propuesta = catalogo.crear_propuesta()
    producto_id = None
    try:
        primera = client.post(
            "/api/v1/productos",
            headers=_auth_headers(admin),
            json=catalogo.payload(producto_proveedor_id=propuesta.id),
        )
        assert primera.status_code == 201
        producto_id = primera.json()["id"]

        segunda = client.post(
            "/api/v1/productos",
            headers=_auth_headers(admin),
            json=catalogo.payload(producto_proveedor_id=propuesta.id),
        )
        assert segunda.status_code == 409
    finally:
        if producto_id:
            _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Editar / activar-desactivar producto
# --------------------------------------------------------------------------


def test_editar_producto_regenera_variantes_al_cambiar_tallas_o_colores():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    creado = client.post(
        "/api/v1/productos", headers=_auth_headers(admin), json=catalogo.payload()
    )
    producto_id = creado.json()["id"]
    try:
        response = client.put(
            f"/api/v1/productos/{producto_id}",
            headers=_auth_headers(admin),
            json=catalogo.payload(
                talla_ids=[catalogo.talla_s.id], color_ids=[catalogo.color_negro.id]
            ),
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["variantes"]) == 1
        assert body["variantes"][0]["talla"]["id"] == catalogo.talla_s.id
        assert body["variantes"][0]["color"]["id"] == catalogo.color_negro.id
    finally:
        _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_activar_desactivar_producto_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    creado = client.post(
        "/api/v1/productos", headers=_auth_headers(admin), json=catalogo.payload()
    )
    producto_id = creado.json()["id"]
    try:
        desactivar = client.patch(
            f"/api/v1/productos/{producto_id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert desactivar.status_code == 200
        assert desactivar.json()["is_active"] is False

        activar = client.patch(
            f"/api/v1/productos/{producto_id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": True},
        )
        assert activar.status_code == 200
        assert activar.json()["is_active"] is True
    finally:
        _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Buscar / filtrar
# --------------------------------------------------------------------------


def test_listar_productos_filtra_por_busqueda_categoria_y_estado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    creado = client.post(
        "/api/v1/productos", headers=_auth_headers(admin), json=catalogo.payload()
    )
    producto = creado.json()
    producto_id = producto["id"]
    try:
        headers = _auth_headers(admin)

        por_busqueda = client.get(
            f"/api/v1/productos?search={producto['nombre'][:8]}", headers=headers
        )
        assert producto_id in {p["id"] for p in por_busqueda.json()}

        por_categoria = client.get(
            f"/api/v1/productos?categoria_id={catalogo.categoria.id}", headers=headers
        )
        assert producto_id in {p["id"] for p in por_categoria.json()}

        client.patch(
            f"/api/v1/productos/{producto_id}/estado", headers=headers, json={"is_active": False}
        )
        activos = client.get("/api/v1/productos?estado=active", headers=headers)
        assert producto_id not in {p["id"] for p in activos.json()}
        inactivos = client.get("/api/v1/productos?estado=inactive", headers=headers)
        assert producto_id in {p["id"] for p in inactivos.json()}
    finally:
        _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_precio_venta_es_el_mismo_para_todas_las_sucursales():
    """precio_venta es un único valor global del producto -- CU08 no crea
    precio por sucursal (ver sección 4 del caso de uso)."""
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    creado = client.post(
        "/api/v1/productos",
        headers=_auth_headers(admin),
        json=catalogo.payload(nombre="Chaqueta Urban", precio_venta="399.00"),
    )
    producto_id = creado.json()["id"]
    try:
        assert creado.json()["precio_venta"] == "399.00"
        obtenido = client.get(f"/api/v1/productos/{producto_id}", headers=_auth_headers(admin))
        assert obtenido.json()["precio_venta"] == "399.00"
    finally:
        _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Imágenes (imagen principal obligatoria + imágenes adicionales opcionales)
# --------------------------------------------------------------------------

_CONTENIDO_IMAGEN_FALSA = b"contenido-de-prueba-no-es-una-imagen-real"


def test_establecer_imagen_principal_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    creado = client.post("/api/v1/productos", headers=_auth_headers(admin), json=catalogo.payload())
    producto_id = creado.json()["id"]
    assert creado.json()["imagen_principal_url"] is None
    try:
        response = client.post(
            f"/api/v1/productos/{producto_id}/imagen-principal",
            headers=_auth_headers(admin),
            files={"archivo": ("foto.png", _CONTENIDO_IMAGEN_FALSA, "image/png")},
        )
        assert response.status_code == 200
        url = response.json()["imagen_principal_url"]
        assert url is not None
        assert url.startswith("/api/v1/media/productos/")
        eliminar_archivo_imagen(url)
    finally:
        _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_establecer_imagen_principal_con_formato_invalido_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    creado = client.post("/api/v1/productos", headers=_auth_headers(admin), json=catalogo.payload())
    producto_id = creado.json()["id"]
    try:
        response = client.post(
            f"/api/v1/productos/{producto_id}/imagen-principal",
            headers=_auth_headers(admin),
            files={"archivo": ("archivo.pdf", _CONTENIDO_IMAGEN_FALSA, "application/pdf")},
        )
        assert response.status_code == 422
    finally:
        _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_reemplazar_imagen_principal_borra_el_archivo_anterior():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    creado = client.post("/api/v1/productos", headers=_auth_headers(admin), json=catalogo.payload())
    producto_id = creado.json()["id"]
    try:
        primera = client.post(
            f"/api/v1/productos/{producto_id}/imagen-principal",
            headers=_auth_headers(admin),
            files={"archivo": ("foto1.png", _CONTENIDO_IMAGEN_FALSA, "image/png")},
        )
        url_anterior = primera.json()["imagen_principal_url"]
        ruta_anterior = UPLOADS_ROOT / url_anterior.removeprefix("/api/v1/media/")
        assert ruta_anterior.exists()

        segunda = client.post(
            f"/api/v1/productos/{producto_id}/imagen-principal",
            headers=_auth_headers(admin),
            files={"archivo": ("foto2.png", _CONTENIDO_IMAGEN_FALSA, "image/png")},
        )
        url_nueva = segunda.json()["imagen_principal_url"]

        assert url_nueva != url_anterior
        assert not ruta_anterior.exists()
        eliminar_archivo_imagen(url_nueva)
    finally:
        _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_agregar_y_eliminar_imagen_adicional_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    creado = client.post("/api/v1/productos", headers=_auth_headers(admin), json=catalogo.payload())
    producto_id = creado.json()["id"]
    try:
        agregada = client.post(
            f"/api/v1/productos/{producto_id}/imagenes",
            headers=_auth_headers(admin),
            files={"archivo": ("adicional.webp", _CONTENIDO_IMAGEN_FALSA, "image/webp")},
        )
        assert agregada.status_code == 201
        imagenes = agregada.json()["imagenes"]
        assert len(imagenes) == 1
        imagen_id = imagenes[0]["id"]
        ruta = UPLOADS_ROOT / imagenes[0]["url"].removeprefix("/api/v1/media/")
        assert ruta.exists()

        eliminada = client.delete(
            f"/api/v1/productos/{producto_id}/imagenes/{imagen_id}", headers=_auth_headers(admin)
        )
        assert eliminada.status_code == 200
        assert eliminada.json()["imagenes"] == []
        assert not ruta.exists()
    finally:
        _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)


def test_eliminar_imagen_adicional_inexistente_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    catalogo = _Catalogo()
    creado = client.post("/api/v1/productos", headers=_auth_headers(admin), json=catalogo.payload())
    producto_id = creado.json()["id"]
    try:
        response = client.delete(
            f"/api/v1/productos/{producto_id}/imagenes/9999999", headers=_auth_headers(admin)
        )
        assert response.status_code == 404
    finally:
        _delete_test_producto(producto_id)
        catalogo.cleanup()
        _delete_test_user(admin.id)
