"""Pruebas de CU06 - Gestionar sucursales."""

import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
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


def _create_test_ciudad(nombre: str | None = None, departamento: str = "Santa Cruz") -> Ciudad:
    db = SessionLocal()
    try:
        ciudad = Ciudad(
            nombre=nombre or f"Ciudad {uuid.uuid4().hex[:8]}",
            departamento=departamento,
            is_active=True,
        )
        db.add(ciudad)
        db.commit()
        db.refresh(ciudad)
        return ciudad
    finally:
        db.close()


def _delete_test_ciudad(ciudad_id: int) -> None:
    db = SessionLocal()
    try:
        ciudad = db.get(Ciudad, ciudad_id)
        if ciudad is not None:
            db.delete(ciudad)
            db.commit()
    finally:
        db.close()


def _delete_test_sucursal(sucursal_id: int) -> None:
    db = SessionLocal()
    try:
        sucursal = db.get(Sucursal, sucursal_id)
        if sucursal is not None:
            db.delete(sucursal)
            db.commit()
    finally:
        db.close()


_PAYLOAD_BASE = {"direccion": "Av. Siempre Viva 123", "telefono": "70012345"}


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_listar_sucursales_sin_token_es_rechazado():
    response = client.get("/api/v1/sucursales")
    assert response.status_code == 401


def test_listar_sucursales_con_rol_no_autorizado_es_rechazado():
    cajero = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.get("/api/v1/sucursales", headers=_auth_headers(cajero))
        assert response.status_code == 403
    finally:
        _delete_test_user(cajero.id)


def test_administrador_autorizado_si_puede_listar():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get("/api/v1/sucursales", headers=_auth_headers(admin))
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        _delete_test_user(admin.id)


def test_listar_ciudades_requiere_administrador():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get("/api/v1/ciudades", headers=_auth_headers(admin))
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        _delete_test_user(admin.id)


def test_listar_ciudades_sin_token_es_rechazado():
    response = client.get("/api/v1/ciudades")
    assert response.status_code == 401


# --------------------------------------------------------------------------
# Gestionar ciudades
# --------------------------------------------------------------------------


def test_crear_ciudad_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    nombre = f"Ciudad {uuid.uuid4().hex[:8]}"
    ciudad_id = None
    try:
        response = client.post(
            "/api/v1/ciudades",
            headers=_auth_headers(admin),
            json={"nombre": nombre, "departamento": "Tarija"},
        )
        assert response.status_code == 201
        body = response.json()
        ciudad_id = body["id"]
        assert body["nombre"] == nombre
        assert body["departamento"] == "Tarija"
        assert body["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        if ciudad_id:
            _delete_test_ciudad(ciudad_id)


def test_crear_ciudad_con_nombre_duplicado_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    try:
        response = client.post(
            "/api/v1/ciudades",
            headers=_auth_headers(admin),
            json={"nombre": ciudad.nombre.upper(), "departamento": "Otro"},
        )
        assert response.status_code == 409
    finally:
        _delete_test_user(admin.id)
        _delete_test_ciudad(ciudad.id)


def test_activar_desactivar_ciudad_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    try:
        desactivar = client.patch(
            f"/api/v1/ciudades/{ciudad.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert desactivar.status_code == 200
        assert desactivar.json()["is_active"] is False

        activar = client.patch(
            f"/api/v1/ciudades/{ciudad.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": True},
        )
        assert activar.status_code == 200
        assert activar.json()["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        _delete_test_ciudad(ciudad.id)


def test_desactivar_ciudad_filtra_del_listado_activo():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    try:
        client.patch(
            f"/api/v1/ciudades/{ciudad.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        headers = _auth_headers(admin)

        activas = client.get("/api/v1/ciudades?estado=active", headers=headers)
        assert ciudad.id not in [c["id"] for c in activas.json()]

        inactivas = client.get("/api/v1/ciudades?estado=inactive", headers=headers)
        assert ciudad.id in [c["id"] for c in inactivas.json()]
    finally:
        _delete_test_user(admin.id)
        _delete_test_ciudad(ciudad.id)


# --------------------------------------------------------------------------
# Registrar sucursal
# --------------------------------------------------------------------------


def test_crear_sucursal_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal_id = None
    try:
        response = client.post(
            "/api/v1/sucursales",
            headers=_auth_headers(admin),
            json={"nombre": "Sucursal Centro", "ciudad_id": ciudad.id, **_PAYLOAD_BASE},
        )
        assert response.status_code == 201
        body = response.json()
        sucursal_id = body["id"]
        assert body["nombre"] == "Sucursal Centro"
        assert body["is_active"] is True
        assert body["ciudad"]["id"] == ciudad.id
        assert body["ciudad"]["nombre"] == ciudad.nombre
    finally:
        _delete_test_user(admin.id)
        if sucursal_id:
            _delete_test_sucursal(sucursal_id)
        _delete_test_ciudad(ciudad.id)


def test_crear_sucursal_con_ciudad_inexistente_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/sucursales",
            headers=_auth_headers(admin),
            json={"nombre": "Sucursal Fantasma", "ciudad_id": 9_999_999, **_PAYLOAD_BASE},
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


def test_crear_sucursal_con_nombre_duplicado_en_misma_ciudad_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal_id = None
    try:
        primera = client.post(
            "/api/v1/sucursales",
            headers=_auth_headers(admin),
            json={"nombre": "Sucursal Centro", "ciudad_id": ciudad.id, **_PAYLOAD_BASE},
        )
        sucursal_id = primera.json()["id"]

        duplicada = client.post(
            "/api/v1/sucursales",
            headers=_auth_headers(admin),
            json={"nombre": "sucursal centro", "ciudad_id": ciudad.id, **_PAYLOAD_BASE},
        )
        assert duplicada.status_code == 409
    finally:
        _delete_test_user(admin.id)
        if sucursal_id:
            _delete_test_sucursal(sucursal_id)
        _delete_test_ciudad(ciudad.id)


def test_mismo_nombre_en_ciudades_distintas_es_permitido():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad_a = _create_test_ciudad()
    ciudad_b = _create_test_ciudad()
    ids = []
    try:
        for ciudad in (ciudad_a, ciudad_b):
            response = client.post(
                "/api/v1/sucursales",
                headers=_auth_headers(admin),
                json={"nombre": "Sucursal Centro", "ciudad_id": ciudad.id, **_PAYLOAD_BASE},
            )
            assert response.status_code == 201
            ids.append(response.json()["id"])
    finally:
        _delete_test_user(admin.id)
        for sucursal_id in ids:
            _delete_test_sucursal(sucursal_id)
        _delete_test_ciudad(ciudad_a.id)
        _delete_test_ciudad(ciudad_b.id)


def test_crear_sucursal_con_telefono_invalido_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    try:
        response = client.post(
            "/api/v1/sucursales",
            headers=_auth_headers(admin),
            json={
                "nombre": "Sucursal Centro",
                "ciudad_id": ciudad.id,
                "direccion": "Av. Siempre Viva 123",
                "telefono": "abc",
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)
        _delete_test_ciudad(ciudad.id)


# --------------------------------------------------------------------------
# Editar sucursal
# --------------------------------------------------------------------------


def test_editar_sucursal_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    creada = client.post(
        "/api/v1/sucursales",
        headers=_auth_headers(admin),
        json={"nombre": "Sucursal Original", "ciudad_id": ciudad.id, **_PAYLOAD_BASE},
    )
    sucursal_id = creada.json()["id"]
    try:
        response = client.put(
            f"/api/v1/sucursales/{sucursal_id}",
            headers=_auth_headers(admin),
            json={
                "nombre": "Sucursal Editada",
                "ciudad_id": ciudad.id,
                "direccion": "Nueva dirección 456",
                "telefono": "70099999",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["nombre"] == "Sucursal Editada"
        assert body["direccion"] == "Nueva dirección 456"
    finally:
        _delete_test_user(admin.id)
        _delete_test_sucursal(sucursal_id)
        _delete_test_ciudad(ciudad.id)


# --------------------------------------------------------------------------
# Activar / desactivar
# --------------------------------------------------------------------------


def test_activar_desactivar_sucursal_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    creada = client.post(
        "/api/v1/sucursales",
        headers=_auth_headers(admin),
        json={"nombre": "Sucursal Estado", "ciudad_id": ciudad.id, **_PAYLOAD_BASE},
    )
    sucursal_id = creada.json()["id"]
    try:
        desactivar = client.patch(
            f"/api/v1/sucursales/{sucursal_id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert desactivar.status_code == 200
        assert desactivar.json()["is_active"] is False

        activar = client.patch(
            f"/api/v1/sucursales/{sucursal_id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": True},
        )
        assert activar.status_code == 200
        assert activar.json()["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        _delete_test_sucursal(sucursal_id)
        _delete_test_ciudad(ciudad.id)


# --------------------------------------------------------------------------
# Búsqueda / filtros
# --------------------------------------------------------------------------


def test_listar_sucursales_filtra_por_busqueda_ciudad_y_estado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad_a = _create_test_ciudad()
    ciudad_b = _create_test_ciudad()
    sucursal_a = client.post(
        "/api/v1/sucursales",
        headers=_auth_headers(admin),
        json={"nombre": "Sucursal Alfa", "ciudad_id": ciudad_a.id, **_PAYLOAD_BASE},
    ).json()
    sucursal_b = client.post(
        "/api/v1/sucursales",
        headers=_auth_headers(admin),
        json={"nombre": "Sucursal Beta", "ciudad_id": ciudad_b.id, **_PAYLOAD_BASE},
    ).json()
    client.patch(
        f"/api/v1/sucursales/{sucursal_b['id']}/estado",
        headers=_auth_headers(admin),
        json={"is_active": False},
    )
    try:
        headers = _auth_headers(admin)

        por_busqueda = client.get("/api/v1/sucursales?search=alfa", headers=headers)
        nombres = [s["nombre"] for s in por_busqueda.json()]
        assert "Sucursal Alfa" in nombres
        assert "Sucursal Beta" not in nombres

        por_ciudad = client.get(f"/api/v1/sucursales?ciudad_id={ciudad_a.id}", headers=headers)
        nombres_ciudad = [s["nombre"] for s in por_ciudad.json()]
        assert "Sucursal Alfa" in nombres_ciudad
        assert "Sucursal Beta" not in nombres_ciudad

        por_estado = client.get("/api/v1/sucursales?estado=inactive", headers=headers)
        nombres_estado = [s["nombre"] for s in por_estado.json()]
        assert "Sucursal Beta" in nombres_estado
        assert "Sucursal Alfa" not in nombres_estado
    finally:
        _delete_test_user(admin.id)
        _delete_test_sucursal(sucursal_a["id"])
        _delete_test_sucursal(sucursal_b["id"])
        _delete_test_ciudad(ciudad_a.id)
        _delete_test_ciudad(ciudad_b.id)
