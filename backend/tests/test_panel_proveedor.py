"""Pruebas del Panel del Proveedor.

Énfasis en seguridad: un PROVEEDOR solo debe ver/modificar SU proveedor y SUS
productos enviados, incluso si intenta acceder a un id ajeno manualmente.
"""

import uuid
from datetime import date

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
from modules.P1_SucursalesYCatalogos.Models.producto_proveedor import ProductoProveedor
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.temporada import Temporada
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


def _create_test_temporada() -> Temporada:
    db = SessionLocal()
    try:
        temporada = Temporada(
            nombre=f"Temporada {uuid.uuid4().hex[:8]}",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
            is_active=True,
        )
        db.add(temporada)
        db.commit()
        db.refresh(temporada)
        return temporada
    finally:
        db.close()


def _delete_test_temporada(temporada_id: int) -> None:
    db = SessionLocal()
    try:
        temporada = db.get(Temporada, temporada_id)
        if temporada is not None:
            db.delete(temporada)
            db.commit()
    finally:
        db.close()


def _create_test_coleccion(temporada_id: int) -> Coleccion:
    db = SessionLocal()
    try:
        coleccion = Coleccion(
            nombre=f"Coleccion {uuid.uuid4().hex[:8]}", temporada_id=temporada_id, is_active=True
        )
        db.add(coleccion)
        db.commit()
        db.refresh(coleccion)
        return coleccion
    finally:
        db.close()


def _delete_test_coleccion(coleccion_id: int) -> None:
    db = SessionLocal()
    try:
        coleccion = db.get(Coleccion, coleccion_id)
        if coleccion is not None:
            db.delete(coleccion)
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
    """Agrupa proveedor + usuario PROVEEDOR + temporada + colección de prueba."""

    def __init__(self):
        self.proveedor = _create_test_proveedor()
        self.usuario = _create_test_user(RolUsuario.PROVEEDOR, proveedor_id=self.proveedor.id)
        self.temporada = _create_test_temporada()
        self.coleccion = _create_test_coleccion(self.temporada.id)
        self.producto_ids: list[int] = []

    def headers(self) -> dict:
        return _auth_headers(self.usuario)

    def cleanup(self) -> None:
        for pid in self.producto_ids:
            _delete_test_producto(pid)
        _delete_test_user(self.usuario.id)
        _delete_test_proveedor(self.proveedor.id)
        _delete_test_coleccion(self.coleccion.id)
        _delete_test_temporada(self.temporada.id)


_PAYLOAD_BASE = lambda ctx: {  # noqa: E731
    "nombre": "Chaqueta de prueba",
    "descripcion": "Prenda de prueba",
    "temporada_id": ctx.temporada.id,
    "coleccion_id": ctx.coleccion.id,
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
# Temporadas / colecciones (deben venir de CU10)
# --------------------------------------------------------------------------


def test_listar_temporadas_disponibles_ok():
    ctx = _Contexto()
    try:
        response = client.get("/api/v1/proveedores/panel/temporadas", headers=ctx.headers())
        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert ctx.temporada.id in ids
    finally:
        ctx.cleanup()


def test_listar_colecciones_por_temporada_ok():
    ctx = _Contexto()
    try:
        response = client.get(
            f"/api/v1/proveedores/panel/colecciones?temporada_id={ctx.temporada.id}", headers=ctx.headers()
        )
        assert response.status_code == 200
        ids = [c["id"] for c in response.json()]
        assert ctx.coleccion.id in ids
    finally:
        ctx.cleanup()


# --------------------------------------------------------------------------
# Enviar producto
# --------------------------------------------------------------------------


def test_enviar_producto_ok():
    ctx = _Contexto()
    try:
        response = client.post(
            "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE(ctx)
        )
        assert response.status_code == 201
        body = response.json()
        ctx.producto_ids.append(body["id"])
        assert body["nombre"] == "Chaqueta de prueba"
        assert body["temporada"]["id"] == ctx.temporada.id
        assert body["coleccion"]["id"] == ctx.coleccion.id
        assert body["disponibilidad"] is True
        assert body["is_active"] is True
    finally:
        ctx.cleanup()


def test_enviar_producto_con_coleccion_de_otra_temporada_es_rechazado():
    ctx = _Contexto()
    otra_temporada = _create_test_temporada()
    try:
        response = client.post(
            "/api/v1/proveedores/panel/productos",
            headers=ctx.headers(),
            json={**_PAYLOAD_BASE(ctx), "temporada_id": otra_temporada.id},
        )
        assert response.status_code == 422
    finally:
        ctx.cleanup()
        _delete_test_temporada(otra_temporada.id)


def test_enviar_producto_con_temporada_inexistente_es_rechazado():
    ctx = _Contexto()
    try:
        response = client.post(
            "/api/v1/proveedores/panel/productos",
            headers=ctx.headers(),
            json={**_PAYLOAD_BASE(ctx), "temporada_id": 9_999_999},
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
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE(ctx)
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
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE(ctx)
    )
    producto_id = creado.json()["id"]
    ctx.producto_ids.append(producto_id)
    try:
        response = client.put(
            f"/api/v1/proveedores/panel/productos/{producto_id}",
            headers=ctx.headers(),
            json={**_PAYLOAD_BASE(ctx), "nombre": "Chaqueta Editada"},
        )
        assert response.status_code == 200
        assert response.json()["nombre"] == "Chaqueta Editada"
    finally:
        ctx.cleanup()


def test_cambiar_disponibilidad_ok():
    ctx = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE(ctx)
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
        "/api/v1/proveedores/panel/productos", headers=ctx.headers(), json=_PAYLOAD_BASE(ctx)
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
        "/api/v1/proveedores/panel/productos", headers=ctx_a.headers(), json=_PAYLOAD_BASE(ctx_a)
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
        "/api/v1/proveedores/panel/productos", headers=ctx_a.headers(), json=_PAYLOAD_BASE(ctx_a)
    )
    producto_id = creado.json()["id"]
    ctx_a.producto_ids.append(producto_id)
    try:
        response = client.put(
            f"/api/v1/proveedores/panel/productos/{producto_id}",
            headers=ctx_b.headers(),
            json={**_PAYLOAD_BASE(ctx_b), "nombre": "Intento Ajeno"},
        )
        assert response.status_code == 404
    finally:
        ctx_a.cleanup()
        ctx_b.cleanup()


def test_proveedor_no_puede_cambiar_disponibilidad_de_otro_proveedor():
    ctx_a = _Contexto()
    ctx_b = _Contexto()
    creado = client.post(
        "/api/v1/proveedores/panel/productos", headers=ctx_a.headers(), json=_PAYLOAD_BASE(ctx_a)
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
        "/api/v1/proveedores/panel/productos", headers=ctx_a.headers(), json=_PAYLOAD_BASE(ctx_a)
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
