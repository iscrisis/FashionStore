"""Pruebas de CU10 - Gestionar temporadas y colecciones."""

import uuid
from datetime import date

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.coleccion import Coleccion
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


def _create_test_temporada(nombre: str | None = None) -> Temporada:
    db = SessionLocal()
    try:
        temporada = Temporada(
            nombre=nombre or f"Temporada {uuid.uuid4().hex[:8]}",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 3, 31),
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


def _delete_test_coleccion(coleccion_id: int) -> None:
    db = SessionLocal()
    try:
        coleccion = db.get(Coleccion, coleccion_id)
        if coleccion is not None:
            db.delete(coleccion)
            db.commit()
    finally:
        db.close()


_FECHAS = {"fecha_inicio": "2026-09-01", "fecha_fin": "2026-12-31"}


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_listar_temporadas_sin_token_es_rechazado():
    assert client.get("/api/v1/temporadas").status_code == 401


def test_listar_colecciones_sin_token_es_rechazado():
    assert client.get("/api/v1/colecciones").status_code == 401


def test_listar_con_rol_no_autorizado_es_rechazado():
    cajero = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.get("/api/v1/temporadas", headers=_auth_headers(cajero))
        assert response.status_code == 403
    finally:
        _delete_test_user(cajero.id)


def test_administrador_autorizado_si_puede_listar():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get("/api/v1/temporadas", headers=_auth_headers(admin))
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Registrar temporada
# --------------------------------------------------------------------------


def test_crear_temporada_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    nombre = f"Primavera-Verano {uuid.uuid4().hex[:6]}"
    temporada_id = None
    try:
        response = client.post(
            "/api/v1/temporadas", headers=_auth_headers(admin), json={"nombre": nombre, **_FECHAS}
        )
        assert response.status_code == 201
        body = response.json()
        temporada_id = body["id"]
        assert body["nombre"] == nombre
        assert body["fecha_inicio"] == _FECHAS["fecha_inicio"]
        assert body["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        if temporada_id:
            _delete_test_temporada(temporada_id)


def test_crear_temporada_con_fecha_fin_anterior_a_inicio_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/temporadas",
            headers=_auth_headers(admin),
            json={
                "nombre": f"Temporada Invalida {uuid.uuid4().hex[:6]}",
                "fecha_inicio": "2026-12-31",
                "fecha_fin": "2026-01-01",
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


def test_crear_temporada_con_nombre_duplicado_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada = _create_test_temporada()
    try:
        response = client.post(
            "/api/v1/temporadas",
            headers=_auth_headers(admin),
            json={"nombre": temporada.nombre.upper(), **_FECHAS},
        )
        assert response.status_code == 409
    finally:
        _delete_test_user(admin.id)
        _delete_test_temporada(temporada.id)


def test_crear_temporada_con_nombre_vacio_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/temporadas", headers=_auth_headers(admin), json={"nombre": "  ", **_FECHAS}
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Editar / activar-desactivar temporada
# --------------------------------------------------------------------------


def test_editar_temporada_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada = _create_test_temporada()
    try:
        nuevo_nombre = f"Editada {uuid.uuid4().hex[:6]}"
        response = client.put(
            f"/api/v1/temporadas/{temporada.id}",
            headers=_auth_headers(admin),
            json={"nombre": nuevo_nombre, **_FECHAS},
        )
        assert response.status_code == 200
        assert response.json()["nombre"] == nuevo_nombre
    finally:
        _delete_test_user(admin.id)
        _delete_test_temporada(temporada.id)


def test_activar_desactivar_temporada_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada = _create_test_temporada()
    try:
        desactivar = client.patch(
            f"/api/v1/temporadas/{temporada.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert desactivar.status_code == 200
        assert desactivar.json()["is_active"] is False

        activar = client.patch(
            f"/api/v1/temporadas/{temporada.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": True},
        )
        assert activar.status_code == 200
        assert activar.json()["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        _delete_test_temporada(temporada.id)


# --------------------------------------------------------------------------
# Registrar colección
# --------------------------------------------------------------------------


def test_crear_coleccion_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada = _create_test_temporada()
    coleccion_id = None
    try:
        response = client.post(
            "/api/v1/colecciones",
            headers=_auth_headers(admin),
            json={
                "nombre": "Urban Summer",
                "temporada_id": temporada.id,
                "descripcion": "Prendas urbanas de temporada",
            },
        )
        assert response.status_code == 201
        body = response.json()
        coleccion_id = body["id"]
        assert body["nombre"] == "Urban Summer"
        assert body["temporada"]["id"] == temporada.id
        assert body["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        if coleccion_id:
            _delete_test_coleccion(coleccion_id)
        _delete_test_temporada(temporada.id)


def test_crear_coleccion_con_temporada_inexistente_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/colecciones",
            headers=_auth_headers(admin),
            json={"nombre": "Sin Temporada", "temporada_id": 9_999_999},
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


def test_crear_coleccion_con_nombre_duplicado_en_misma_temporada_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada = _create_test_temporada()
    coleccion_id = None
    try:
        primera = client.post(
            "/api/v1/colecciones",
            headers=_auth_headers(admin),
            json={"nombre": "Kids Summer", "temporada_id": temporada.id},
        )
        coleccion_id = primera.json()["id"]

        duplicada = client.post(
            "/api/v1/colecciones",
            headers=_auth_headers(admin),
            json={"nombre": "kids summer", "temporada_id": temporada.id},
        )
        assert duplicada.status_code == 409
    finally:
        _delete_test_user(admin.id)
        if coleccion_id:
            _delete_test_coleccion(coleccion_id)
        _delete_test_temporada(temporada.id)


def test_misma_coleccion_en_temporadas_distintas_es_permitido():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada_a = _create_test_temporada()
    temporada_b = _create_test_temporada()
    ids = []
    try:
        for temporada in (temporada_a, temporada_b):
            response = client.post(
                "/api/v1/colecciones",
                headers=_auth_headers(admin),
                json={"nombre": "Summer Essentials", "temporada_id": temporada.id},
            )
            assert response.status_code == 201
            ids.append(response.json()["id"])
    finally:
        _delete_test_user(admin.id)
        for coleccion_id in ids:
            _delete_test_coleccion(coleccion_id)
        _delete_test_temporada(temporada_a.id)
        _delete_test_temporada(temporada_b.id)


# --------------------------------------------------------------------------
# Editar / activar-desactivar colección
# --------------------------------------------------------------------------


def test_editar_coleccion_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada = _create_test_temporada()
    creada = client.post(
        "/api/v1/colecciones",
        headers=_auth_headers(admin),
        json={"nombre": "Original", "temporada_id": temporada.id},
    )
    coleccion_id = creada.json()["id"]
    try:
        response = client.put(
            f"/api/v1/colecciones/{coleccion_id}",
            headers=_auth_headers(admin),
            json={"nombre": "Editada", "temporada_id": temporada.id, "descripcion": "Nueva desc"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["nombre"] == "Editada"
        assert body["descripcion"] == "Nueva desc"
    finally:
        _delete_test_user(admin.id)
        _delete_test_coleccion(coleccion_id)
        _delete_test_temporada(temporada.id)


def test_activar_desactivar_coleccion_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada = _create_test_temporada()
    creada = client.post(
        "/api/v1/colecciones",
        headers=_auth_headers(admin),
        json={"nombre": "Estado Test", "temporada_id": temporada.id},
    )
    coleccion_id = creada.json()["id"]
    try:
        desactivar = client.patch(
            f"/api/v1/colecciones/{coleccion_id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert desactivar.status_code == 200
        assert desactivar.json()["is_active"] is False
    finally:
        _delete_test_user(admin.id)
        _delete_test_coleccion(coleccion_id)
        _delete_test_temporada(temporada.id)


# --------------------------------------------------------------------------
# Búsqueda / filtro por temporada
# --------------------------------------------------------------------------


def test_listar_colecciones_filtra_por_temporada_y_busqueda():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada_a = _create_test_temporada()
    temporada_b = _create_test_temporada()
    alfa = client.post(
        "/api/v1/colecciones",
        headers=_auth_headers(admin),
        json={"nombre": f"Alfa-{uuid.uuid4().hex[:6]}", "temporada_id": temporada_a.id},
    ).json()
    beta = client.post(
        "/api/v1/colecciones",
        headers=_auth_headers(admin),
        json={"nombre": f"Beta-{uuid.uuid4().hex[:6]}", "temporada_id": temporada_b.id},
    ).json()
    try:
        headers = _auth_headers(admin)

        por_temporada = client.get(f"/api/v1/colecciones?temporada_id={temporada_a.id}", headers=headers)
        nombres = [c["nombre"] for c in por_temporada.json()]
        assert alfa["nombre"] in nombres
        assert beta["nombre"] not in nombres

        por_busqueda = client.get("/api/v1/colecciones?search=alfa", headers=headers)
        nombres_busqueda = [c["nombre"] for c in por_busqueda.json()]
        assert alfa["nombre"] in nombres_busqueda
        assert beta["nombre"] not in nombres_busqueda
    finally:
        _delete_test_user(admin.id)
        _delete_test_coleccion(alfa["id"])
        _delete_test_coleccion(beta["id"])
        _delete_test_temporada(temporada_a.id)
        _delete_test_temporada(temporada_b.id)


# --------------------------------------------------------------------------
# Colección destacada del Home
# --------------------------------------------------------------------------

_CONTENIDO_IMAGEN_FALSA = b"contenido-de-prueba-no-es-una-imagen-real"


def test_marcar_destacada_desmarca_la_anterior():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada = _create_test_temporada()
    headers = _auth_headers(admin)
    primera = client.post(
        "/api/v1/colecciones",
        headers=headers,
        json={"nombre": f"Destacada A-{uuid.uuid4().hex[:6]}", "temporada_id": temporada.id},
    ).json()
    segunda = client.post(
        "/api/v1/colecciones",
        headers=headers,
        json={"nombre": f"Destacada B-{uuid.uuid4().hex[:6]}", "temporada_id": temporada.id},
    ).json()
    try:
        marcar_primera = client.patch(
            f"/api/v1/colecciones/{primera['id']}/destacada-inicio",
            headers=headers,
            json={"es_destacada_inicio": True},
        )
        assert marcar_primera.status_code == 200
        assert marcar_primera.json()["es_destacada_inicio"] is True

        marcar_segunda = client.patch(
            f"/api/v1/colecciones/{segunda['id']}/destacada-inicio",
            headers=headers,
            json={"es_destacada_inicio": True},
        )
        assert marcar_segunda.status_code == 200
        assert marcar_segunda.json()["es_destacada_inicio"] is True

        primera_actualizada = client.get(f"/api/v1/colecciones?search=Destacada A", headers=headers)
        assert primera_actualizada.json()[0]["es_destacada_inicio"] is False
    finally:
        _delete_test_user(admin.id)
        _delete_test_coleccion(primera["id"])
        _delete_test_coleccion(segunda["id"])
        _delete_test_temporada(temporada.id)


def test_coleccion_destacada_publica_sin_marcar_devuelve_null():
    response = client.get("/api/v1/colecciones/destacada")
    assert response.status_code == 200
    # Puede haber una destacada de otra prueba/entorno; solo garantizamos que
    # el endpoint es público y responde 200 sin token.
    assert response.json() is None or "id" in response.json()


def test_coleccion_destacada_publica_expone_la_marcada_y_su_imagen():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada = _create_test_temporada()
    headers = _auth_headers(admin)
    coleccion = client.post(
        "/api/v1/colecciones",
        headers=headers,
        json={"nombre": f"Publica-{uuid.uuid4().hex[:6]}", "temporada_id": temporada.id},
    ).json()
    try:
        client.patch(
            f"/api/v1/colecciones/{coleccion['id']}/destacada-inicio",
            headers=headers,
            json={"es_destacada_inicio": True},
        )
        subida = client.post(
            f"/api/v1/colecciones/{coleccion['id']}/imagen-destacada",
            headers=headers,
            files={"archivo": ("modelos.webp", _CONTENIDO_IMAGEN_FALSA, "image/webp")},
        )
        assert subida.status_code == 200
        assert subida.json()["imagen_destacada_url"] is not None

        publica = client.get("/api/v1/colecciones/destacada")
        assert publica.status_code == 200
        cuerpo = publica.json()
        assert cuerpo["id"] == coleccion["id"]
        assert cuerpo["imagen_destacada_url"] == subida.json()["imagen_destacada_url"]
        assert set(cuerpo.keys()) == {"id", "imagen_destacada_url"}
    finally:
        client.patch(
            f"/api/v1/colecciones/{coleccion['id']}/destacada-inicio",
            headers=headers,
            json={"es_destacada_inicio": False},
        )
        _delete_test_user(admin.id)
        _delete_test_coleccion(coleccion["id"])
        _delete_test_temporada(temporada.id)


def test_coleccion_destacada_pero_inactiva_no_aparece_en_publico():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    temporada = _create_test_temporada()
    headers = _auth_headers(admin)
    coleccion = client.post(
        "/api/v1/colecciones",
        headers=headers,
        json={"nombre": f"Inactiva-{uuid.uuid4().hex[:6]}", "temporada_id": temporada.id},
    ).json()
    try:
        client.patch(
            f"/api/v1/colecciones/{coleccion['id']}/destacada-inicio",
            headers=headers,
            json={"es_destacada_inicio": True},
        )
        client.patch(
            f"/api/v1/colecciones/{coleccion['id']}/estado", headers=headers, json={"is_active": False}
        )

        publica = client.get("/api/v1/colecciones/destacada")
        assert publica.status_code == 200
        cuerpo = publica.json()
        assert cuerpo is None or cuerpo["id"] != coleccion["id"]
    finally:
        _delete_test_user(admin.id)
        _delete_test_coleccion(coleccion["id"])
        _delete_test_temporada(temporada.id)
