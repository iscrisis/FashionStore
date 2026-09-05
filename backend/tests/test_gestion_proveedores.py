"""Pruebas de Gestión de Proveedores."""

import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
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


def _delete_test_proveedor(proveedor_id: int) -> None:
    db = SessionLocal()
    try:
        proveedor = db.get(Proveedor, proveedor_id)
        if proveedor is not None:
            db.delete(proveedor)
            db.commit()
    finally:
        db.close()


_DATOS_BASE = {"nombre_contacto": "Juan Pérez", "correo": "contacto@textiles.com", "telefono": "70012345"}


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_listar_proveedores_sin_token_es_rechazado():
    assert client.get("/api/v1/proveedores").status_code == 401


def test_listar_con_rol_no_autorizado_es_rechazado():
    cajero = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.get("/api/v1/proveedores", headers=_auth_headers(cajero))
        assert response.status_code == 403
    finally:
        _delete_test_user(cajero.id)


def test_administrador_autorizado_si_puede_listar():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get("/api/v1/proveedores", headers=_auth_headers(admin))
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Registrar
# --------------------------------------------------------------------------


def test_crear_proveedor_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    razon_social = f"Textiles Andinos {uuid.uuid4().hex[:8]}"
    proveedor_id = None
    try:
        response = client.post(
            "/api/v1/proveedores",
            headers=_auth_headers(admin),
            json={"razon_social": razon_social, **_DATOS_BASE},
        )
        assert response.status_code == 201
        body = response.json()
        proveedor_id = body["id"]
        assert body["razon_social"] == razon_social
        assert body["correo"] == _DATOS_BASE["correo"]
        assert body["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        if proveedor_id:
            _delete_test_proveedor(proveedor_id)


def test_crear_proveedor_con_razon_social_duplicada_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    razon_social = f"Textiles Unicos {uuid.uuid4().hex[:8]}"
    primero = client.post(
        "/api/v1/proveedores", headers=_auth_headers(admin), json={"razon_social": razon_social, **_DATOS_BASE}
    )
    proveedor_id = primero.json()["id"]
    try:
        duplicado = client.post(
            "/api/v1/proveedores",
            headers=_auth_headers(admin),
            json={"razon_social": razon_social.upper(), **_DATOS_BASE},
        )
        assert duplicado.status_code == 409
    finally:
        _delete_test_user(admin.id)
        _delete_test_proveedor(proveedor_id)


def test_crear_proveedor_con_correo_invalido_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/proveedores",
            headers=_auth_headers(admin),
            json={
                "razon_social": f"Proveedor {uuid.uuid4().hex[:8]}",
                "nombre_contacto": "Juan Pérez",
                "correo": "no-es-un-correo",
                "telefono": "70012345",
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


def test_crear_proveedor_con_telefono_invalido_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/proveedores",
            headers=_auth_headers(admin),
            json={
                "razon_social": f"Proveedor {uuid.uuid4().hex[:8]}",
                "nombre_contacto": "Juan Pérez",
                "correo": "contacto@proveedor.com",
                "telefono": "abc",
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Consultar / editar
# --------------------------------------------------------------------------


def test_obtener_proveedor_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    creado = client.post(
        "/api/v1/proveedores",
        headers=_auth_headers(admin),
        json={"razon_social": f"Consultable {uuid.uuid4().hex[:8]}", **_DATOS_BASE},
    )
    proveedor_id = creado.json()["id"]
    try:
        response = client.get(f"/api/v1/proveedores/{proveedor_id}", headers=_auth_headers(admin))
        assert response.status_code == 200
        assert response.json()["id"] == proveedor_id
    finally:
        _delete_test_user(admin.id)
        _delete_test_proveedor(proveedor_id)


def test_obtener_proveedor_inexistente_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get("/api/v1/proveedores/9999999", headers=_auth_headers(admin))
        assert response.status_code == 404
    finally:
        _delete_test_user(admin.id)


def test_editar_proveedor_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    creado = client.post(
        "/api/v1/proveedores",
        headers=_auth_headers(admin),
        json={"razon_social": f"Original {uuid.uuid4().hex[:8]}", **_DATOS_BASE},
    )
    proveedor_id = creado.json()["id"]
    try:
        nueva_razon = f"Editado {uuid.uuid4().hex[:8]}"
        response = client.put(
            f"/api/v1/proveedores/{proveedor_id}",
            headers=_auth_headers(admin),
            json={
                "razon_social": nueva_razon,
                "nombre_contacto": "María López",
                "correo": "nuevo@contacto.com",
                "telefono": "70099999",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["razon_social"] == nueva_razon
        assert body["nombre_contacto"] == "María López"
    finally:
        _delete_test_user(admin.id)
        _delete_test_proveedor(proveedor_id)


# --------------------------------------------------------------------------
# Activar / desactivar
# --------------------------------------------------------------------------


def test_activar_desactivar_proveedor_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    creado = client.post(
        "/api/v1/proveedores",
        headers=_auth_headers(admin),
        json={"razon_social": f"Estado {uuid.uuid4().hex[:8]}", **_DATOS_BASE},
    )
    proveedor_id = creado.json()["id"]
    try:
        desactivar = client.patch(
            f"/api/v1/proveedores/{proveedor_id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert desactivar.status_code == 200
        assert desactivar.json()["is_active"] is False

        activar = client.patch(
            f"/api/v1/proveedores/{proveedor_id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": True},
        )
        assert activar.status_code == 200
        assert activar.json()["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        _delete_test_proveedor(proveedor_id)


# --------------------------------------------------------------------------
# Búsqueda / filtros
# --------------------------------------------------------------------------


def test_listar_proveedores_filtra_por_busqueda_y_estado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    alfa = client.post(
        "/api/v1/proveedores",
        headers=_auth_headers(admin),
        json={"razon_social": f"Alfa Textiles {uuid.uuid4().hex[:6]}", **_DATOS_BASE},
    ).json()
    beta = client.post(
        "/api/v1/proveedores",
        headers=_auth_headers(admin),
        json={"razon_social": f"Beta Confecciones {uuid.uuid4().hex[:6]}", **_DATOS_BASE},
    ).json()
    client.patch(
        f"/api/v1/proveedores/{beta['id']}/estado", headers=_auth_headers(admin), json={"is_active": False}
    )
    try:
        headers = _auth_headers(admin)

        por_busqueda = client.get("/api/v1/proveedores?search=alfa", headers=headers)
        nombres = [p["razon_social"] for p in por_busqueda.json()]
        assert alfa["razon_social"] in nombres
        assert beta["razon_social"] not in nombres

        por_estado = client.get("/api/v1/proveedores?estado=inactive", headers=headers)
        nombres_estado = [p["razon_social"] for p in por_estado.json()]
        assert beta["razon_social"] in nombres_estado
        assert alfa["razon_social"] not in nombres_estado
    finally:
        _delete_test_user(admin.id)
        _delete_test_proveedor(alfa["id"])
        _delete_test_proveedor(beta["id"])
