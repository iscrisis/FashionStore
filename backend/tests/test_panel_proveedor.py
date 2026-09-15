"""Pruebas del Panel del Proveedor.

Énfasis en seguridad: un PROVEEDOR solo debe ver/modificar SU proveedor y SUS
productos enviados, incluso si intenta acceder a un id ajeno manualmente.

El proveedor solo propone nombre/descripción/imagen/disponibilidad
(ProductoProveedor); categoría, temporada, colección, precio, tallas y
colores los decide el Administrador al convertir la propuesta en un Producto
real (CU08) -- ver test_gestionar_productos.py para esa parte del flujo.
"""

import io
import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.producto_proveedor import ProductoProveedor
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

client = TestClient(app)


def _create_test_user(rol: RolUsuario, proveedor_id: int | None = None) -> Usuario:
    db = SessionLocal()
    try:
        usuario = Usuario(
            nombre="Usuario de prueba",
            correo=f"test-{uuid.uuid4().hex[:10]}@fashionstore.com",
            password_hash=hash_password("ClaveSegura123!"),
            rol=rol,
            is_active=True,
            proveedor_id=proveedor_id,
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


def _create_test_proveedor() -> Proveedor:
    db = SessionLocal()
    try:
        proveedor = Proveedor(
            razon_social=f"Proveedor {uuid.uuid4().hex[:8]}",
            nombre_contacto="Contacto",
            correo="contacto@proveedor.com",
            telefono="70012345",
            is_active=True,
        )
        db.add(proveedor)
        db.commit()
        db.refresh(proveedor)
        return proveedor
    finally:
        db.close()


def _delete_test_proveedor(proveedor_id: int) -> None:
    db = SessionLocal()
    try:
        proveedor = db.get(Proveedor, proveedor_id)
        if proveedor is not None:
            db.delete(proveedor)
            db.commit()
    finally:
        db.close()


def _delete_test_producto(producto_id: int) -> None:
    db = SessionLocal()
    try:
        producto = db.get(ProductoProveedor, producto_id)
        if producto is not None:
            db.delete(producto)
            db.commit()
    finally:
        db.close()


class _Contexto:
    """Agrupa proveedor + usuario PROVEEDOR de prueba."""

    def __init__(self):
        self.proveedor = _create_test_proveedor()
        self.usuario = _create_test_user(RolUsuario.PROVEEDOR, proveedor_id=self.proveedor.id)
        self.producto_ids: list[int] = []

    def headers(self) -> dict:
        return _auth_headers(self.usuario)

    def cleanup(self) -> None:
        for pid in self.producto_ids:
            _delete_test_producto(pid)
        _delete_test_user(self.usuario.id)
        _delete_test_proveedor(self.proveedor.id)


_PAYLOAD_BASE = {
    "nombre": "Chaqueta de prueba",
    "descripcion": "Prenda de prueba",
}


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_perfil_sin_token_es_rechazado():
    assert client.get("/api/v1/proveedores/panel/perfil").status_code == 401


def test_perfil_con_rol_no_autorizado_es_rechazado():
    cajero = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.get("/api/v1/proveedores/panel/perfil", headers=_auth_headers(cajero))
        assert response.status_code == 403
    finally:
        _delete_test_user(cajero.id)


def test_administrador_no_puede_usar_el_panel_de_proveedor():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get("/api/v1/proveedores/panel/perfil", headers=_auth_headers(admin))
        assert response.status_code == 403
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Mi perfil
# --------------------------------------------------------------------------


def test_obtener_mi_perfil_ok():
    ctx = _Contexto()
    try:
        response = client.get("/api/v1/proveedores/panel/perfil", headers=ctx.headers())
        assert response.status_code == 200
        assert response.json()["id"] == ctx.proveedor.id
    finally:
        ctx.cleanup()


def test_actualizar_mi_perfil_ok():
    ctx = _Contexto()
    try:
        response = client.put(
            "/api/v1/proveedores/panel/perfil",
            headers=ctx.headers(),
            json={
                "razon_social": ctx.proveedor.razon_social,
                "nombre_contacto": "Nuevo Contacto",
                "correo": "nuevo@contacto.com",
                "telefono": "70099999",
            },
        )
        assert response.status_code == 200
        assert response.json()["nombre_contacto"] == "Nuevo Contacto"
    finally:
        ctx.cleanup()


# --------------------------------------------------------------------------
# Enviar producto -- solo nombre/descripción/disponibilidad. Categoría,
# temporada, colección, precio, tallas y colores NO se piden aquí: los
# define el Administrador al convertir la propuesta (CU08).
# --------------------------------------------------------------------------


def test_enviar_producto_ok():
    ctx = _Contexto()
    try:
        response = client.post(
            "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE
        )
        assert response.status_code == 201
        body = response.json()
        ctx.producto_ids.append(body["id"])
        assert body["nombre"] == "Chaqueta de prueba"
        assert body["disponibilidad"] is True
        assert body["is_active"] is True
        # Recién creada: todavía no existe un Producto (CU08) vinculado.
        assert body["estado"] == "PENDIENTE"
        assert body["variantes"] == []
        assert body["imagen_url"] is None
    finally:
        ctx.cleanup()


def test_enviar_producto_sin_nombre_es_rechazado():
    ctx = _Contexto()
    try:
        response = client.post(
            "/api/v1/proveedores/panel/productos",
            headers=ctx.headers(),
            json={**_PAYLOAD_BASE, "nombre": "x"},
        )
        assert response.status_code == 422
    finally:
        ctx.cleanup()


def test_establecer_imagen_ok():
    ctx = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx.producto_ids.append(producto_id)
    try:
        imagen_jpg = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
        )
        response = client.post(
            f"/api/v1/proveedores/panel/productos/{producto_id}/imagen",
            headers=ctx.headers(),
            files={"archivo": ("referencia.jpg", io.BytesIO(imagen_jpg), "image/jpeg")},
        )
        assert response.status_code == 200
        assert response.json()["imagen_url"] is not None
    finally:
        ctx.cleanup()


def test_establecer_imagen_con_archivo_invalido_es_rechazado():
    ctx = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx.producto_ids.append(producto_id)
    try:
        response = client.post(
            f"/api/v1/proveedores/panel/productos/{producto_id}/imagen",
            headers=ctx.headers(),
            files={"archivo": ("archivo.txt", io.BytesIO(b"no es una imagen"), "text/plain")},
        )
        assert response.status_code == 422
    finally:
        ctx.cleanup()


# --------------------------------------------------------------------------
# Consultar / editar mis productos
# --------------------------------------------------------------------------


def test_listar_mis_productos_ok():
    ctx = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE
    )
    ctx.producto_ids.append(creado.json()["id"])
    try:
        response = client.get("/api/v1/proveedores/panel/productos", headers=ctx.headers())
        assert response.status_code == 200
        assert len(response.json()) == 1
    finally:
        ctx.cleanup()


def test_editar_mi_producto_ok():
    ctx = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx.producto_ids.append(producto_id)
    try:
        response = client.put(
            f"/api/v1/proveedores/panel/productos/{producto_id}",
            headers=ctx.headers(),
            json={**_PAYLOAD_BASE, "nombre": "Chaqueta Editada"},
        )
        assert response.status_code == 200
        assert response.json()["nombre"] == "Chaqueta Editada"
    finally:
        ctx.cleanup()


def test_cambiar_disponibilidad_ok():
    ctx = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx.producto_ids.append(producto_id)
    try:
        response = client.patch(
            f"/api/v1/proveedores/panel/productos/{producto_id}/disponibilidad",
            headers=ctx.headers(),
            json={"disponibilidad": False},
        )
        assert response.status_code == 200
        assert response.json()["disponibilidad"] is False
    finally:
        ctx.cleanup()


def test_cambiar_estado_producto_ok():
    ctx = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx.producto_ids.append(producto_id)
    try:
        response = client.patch(
            f"/api/v1/proveedores/panel/productos/{producto_id}/estado",
            headers=ctx.headers(),
            json={"is_active": False},
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False
    finally:
        ctx.cleanup()


# --------------------------------------------------------------------------
# Aislamiento entre proveedores (seguridad)
# --------------------------------------------------------------------------


def test_proveedor_no_puede_ver_producto_de_otro_proveedor():
    ctx_a = _Contexto()
    ctx_b = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx_a.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx_a.producto_ids.append(producto_id)
    try:
        response = client.get(
            f"/api/v1/proveedores/panel/productos/{producto_id}", headers=ctx_b.headers()
        )
        assert response.status_code == 404
    finally:
        ctx_a.cleanup()
        ctx_b.cleanup()


def test_proveedor_no_puede_editar_producto_de_otro_proveedor():
    ctx_a = _Contexto()
    ctx_b = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx_a.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx_a.producto_ids.append(producto_id)
    try:
        response = client.put(
            f"/api/v1/proveedores/panel/productos/{producto_id}",
            headers=ctx_b.headers(),
            json={**_PAYLOAD_BASE, "nombre": "Intento Ajeno"},
        )
        assert response.status_code == 404
    finally:
        ctx_a.cleanup()
        ctx_b.cleanup()


def test_proveedor_no_puede_cambiar_disponibilidad_de_otro_proveedor():
    ctx_a = _Contexto()
    ctx_b = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx_a.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx_a.producto_ids.append(producto_id)
    try:
        response = client.patch(
            f"/api/v1/proveedores/panel/productos/{producto_id}/disponibilidad",
            headers=ctx_b.headers(),
            json={"disponibilidad": False},
        )
        assert response.status_code == 404
    finally:
        ctx_a.cleanup()
        ctx_b.cleanup()


def test_listar_mis_productos_no_incluye_los_de_otro_proveedor():
    ctx_a = _Contexto()
    ctx_b = _Contexto()
    creado_a = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx_a.headers(), json=_PAYLOAD_BASE
    )
    ctx_a.producto_ids.append(creado_a.json()["id"])
    try:
        response = client.get("/api/v1/proveedores/panel/productos", headers=ctx_b.headers())
        assert response.status_code == 200
        assert response.json() == []
    finally:
        ctx_a.cleanup()
        ctx_b.cleanup()


def test_proveedor_no_puede_ver_perfil_de_otro_cambiando_nada_ids_no_expuestos():
    # El endpoint /perfil no recibe id en absoluto: siempre resuelve el propio
    # proveedor desde el token. Esta prueba confirma que dos proveedores
    # distintos obtienen efectivamente su propio proveedor, nunca el ajeno.
    ctx_a = _Contexto()
    ctx_b = _Contexto()
    try:
        perfil_a = client.get("/api/v1/proveedores/panel/perfil", headers=ctx_a.headers())
        perfil_b = client.get("/api/v1/proveedores/panel/perfil", headers=ctx_b.headers())
        assert perfil_a.json()["id"] == ctx_a.proveedor.id
        assert perfil_b.json()["id"] == ctx_b.proveedor.id
        assert perfil_a.json()["id"] != perfil_b.json()["id"]
    finally:
        ctx_a.cleanup()
        ctx_b.cleanup()


# --------------------------------------------------------------------------
# Propuesta rechazada -- el proveedor la ve, pero no puede modificarla
# (ver CU08 test_gestionar_productos.py para el lado del Administrador)
# --------------------------------------------------------------------------


def _rechazar_como_admin(producto_id: int) -> None:
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.patch(
            f"/api/v1/productos/propuestas/{producto_id}/rechazar", headers=_auth_headers(admin)
        )
        assert response.status_code == 200
    finally:
        _delete_test_user(admin.id)


def test_proveedor_ve_su_propuesta_como_rechazada():
    ctx = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx.producto_ids.append(producto_id)
    try:
        _rechazar_como_admin(producto_id)

        response = client.get(
            f"/api/v1/proveedores/panel/productos/{producto_id}", headers=ctx.headers()
        )
        assert response.status_code == 200
        assert response.json()["estado"] == "RECHAZADO"
    finally:
        ctx.cleanup()


def test_proveedor_no_puede_editar_propuesta_rechazada():
    ctx = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx.producto_ids.append(producto_id)
    try:
        _rechazar_como_admin(producto_id)

        response = client.put(
            f"/api/v1/proveedores/panel/productos/{producto_id}",
            headers=ctx.headers(),
            json={**_PAYLOAD_BASE, "nombre": "Intento tras rechazo"},
        )
        assert response.status_code == 409
    finally:
        ctx.cleanup()


def test_proveedor_no_puede_cambiar_disponibilidad_de_propuesta_rechazada():
    ctx = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE
    )
    producto_id = creado.json()["id"]
    ctx.producto_ids.append(producto_id)
    try:
        _rechazar_como_admin(producto_id)

        response = client.patch(
            f"/api/v1/proveedores/panel/productos/{producto_id}/disponibilidad",
            headers=ctx.headers(),
            json={"disponibilidad": False},
        )
        assert response.status_code == 409
    finally:
        ctx.cleanup()
