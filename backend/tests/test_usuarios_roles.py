"""Pruebas de CU05 - Gestionar usuarios y roles."""

import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.proveedor import Proveedor
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal
from modules.P2_UsuariosYAccesos.CU05_GestionarUsuariosRoles.repository import (
    UsuariosRolesRepository,
)
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario

client = TestClient(app)


def _create_test_user(rol: RolUsuario, is_active: bool = True, sucursal_id: int | None = None) -> Usuario:
    db = SessionLocal()
    try:
        usuario = Usuario(
            nombre="Usuario de prueba",
            correo=f"test-{uuid.uuid4().hex[:10]}@fashionstore.com",
            password_hash=hash_password("ClaveSegura123!"),
            rol=rol,
            is_active=is_active,
            sucursal_id=sucursal_id,
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


def _create_test_ciudad() -> Ciudad:
    db = SessionLocal()
    try:
        ciudad = Ciudad(nombre=f"Ciudad {uuid.uuid4().hex[:8]}", departamento="Santa Cruz", is_active=True)
        db.add(ciudad)
        db.commit()
        db.refresh(ciudad)
        return ciudad
    finally:
        db.close()


def _create_test_sucursal(ciudad_id: int) -> Sucursal:
    db = SessionLocal()
    try:
        sucursal = Sucursal(
            nombre=f"Sucursal {uuid.uuid4().hex[:8]}",
            ciudad_id=ciudad_id,
            direccion="Av. Siempre Viva 123",
            telefono="70012345",
            is_active=True,
        )
        db.add(sucursal)
        db.commit()
        db.refresh(sucursal)
        return sucursal
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


def _delete_test_ciudad(ciudad_id: int) -> None:
    db = SessionLocal()
    try:
        ciudad = db.get(Ciudad, ciudad_id)
        if ciudad is not None:
            db.delete(ciudad)
            db.commit()
    finally:
        db.close()


def _create_test_proveedor() -> Proveedor:
    db = SessionLocal()
    try:
        proveedor = Proveedor(
            razon_social=f"Proveedor {uuid.uuid4().hex[:8]}",
            nombre_contacto="Contacto de prueba",
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


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_listar_usuarios_sin_token_es_rechazado():
    response = client.get("/api/v1/usuarios")
    assert response.status_code == 401


def test_listar_usuarios_con_rol_no_autorizado_es_rechazado():
    cajero = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.get("/api/v1/usuarios", headers=_auth_headers(cajero))
        assert response.status_code == 403
    finally:
        _delete_test_user(cajero.id)


def test_administrador_autorizado_si_puede_listar():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get("/api/v1/usuarios", headers=_auth_headers(admin))
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Protección del Administrador General
# --------------------------------------------------------------------------


def test_administrador_no_aparece_en_el_listado():
    admin_actor = _create_test_user(RolUsuario.ADMINISTRADOR)
    admin_objetivo = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        headers = _auth_headers(admin_actor)

        listado = client.get("/api/v1/usuarios", headers=headers)
        ids = [u["id"] for u in listado.json()]
        assert admin_objetivo.id not in ids
        assert admin_actor.id not in ids

        # Ni siquiera filtrando explícitamente por rol=ADMINISTRADOR aparece.
        filtrado = client.get("/api/v1/usuarios?rol=ADMINISTRADOR", headers=headers)
        assert filtrado.json() == []
    finally:
        _delete_test_user(admin_actor.id)
        _delete_test_user(admin_objetivo.id)


def test_administrador_general_no_es_una_opcion_al_crear_usuario():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get("/api/v1/usuarios/roles", headers=_auth_headers(admin))
        assert response.status_code == 200
        valores = [r["valor"] for r in response.json()]
        assert "ADMINISTRADOR" not in valores
    finally:
        _delete_test_user(admin.id)


def test_crear_usuario_con_rol_administrador_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Segundo Admin",
                "correo": f"segundo-admin-{uuid.uuid4().hex[:8]}@fashionstore.com",
                "password": "ClaveSegura123!",
                "rol": "ADMINISTRADOR",
                "sucursal_id": sucursal.id,
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


def test_cambiar_rol_a_administrador_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    objetivo = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.patch(
            f"/api/v1/usuarios/{objetivo.id}/rol",
            headers=_auth_headers(admin),
            json={"rol": "ADMINISTRADOR"},
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(objetivo.id)


def test_no_se_puede_obtener_al_administrador_por_id():
    admin_actor = _create_test_user(RolUsuario.ADMINISTRADOR)
    admin_objetivo = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.get(
            f"/api/v1/usuarios/{admin_objetivo.id}", headers=_auth_headers(admin_actor)
        )
        assert response.status_code == 404
    finally:
        _delete_test_user(admin_actor.id)
        _delete_test_user(admin_objetivo.id)


def test_no_se_puede_editar_al_administrador():
    admin_actor = _create_test_user(RolUsuario.ADMINISTRADOR)
    admin_objetivo = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    try:
        response = client.put(
            f"/api/v1/usuarios/{admin_objetivo.id}",
            headers=_auth_headers(admin_actor),
            json={
                "nombre": "Intento de edición",
                "correo": admin_objetivo.correo,
                "sucursal_id": sucursal.id,
            },
        )
        assert response.status_code == 404
    finally:
        _delete_test_user(admin_actor.id)
        _delete_test_user(admin_objetivo.id)
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


def test_no_se_puede_desactivar_al_administrador():
    admin_actor = _create_test_user(RolUsuario.ADMINISTRADOR)
    admin_objetivo = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.patch(
            f"/api/v1/usuarios/{admin_objetivo.id}/estado",
            headers=_auth_headers(admin_actor),
            json={"is_active": False},
        )
        assert response.status_code == 404
    finally:
        _delete_test_user(admin_actor.id)
        _delete_test_user(admin_objetivo.id)


# --------------------------------------------------------------------------
# Listado / búsqueda / filtros
# --------------------------------------------------------------------------


def test_listar_usuarios_filtra_por_rol_y_busqueda():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    cajero = _create_test_user(RolUsuario.CAJERO)
    try:
        headers = _auth_headers(admin)

        respuesta_rol = client.get("/api/v1/usuarios?rol=CAJERO", headers=headers)
        assert respuesta_rol.status_code == 200
        correos = [u["correo"] for u in respuesta_rol.json()]
        assert cajero.correo in correos
        assert admin.correo not in correos

        respuesta_busqueda = client.get(
            f"/api/v1/usuarios?search={cajero.correo.split('@')[0]}", headers=headers
        )
        assert respuesta_busqueda.status_code == 200
        assert any(u["correo"] == cajero.correo for u in respuesta_busqueda.json())
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(cajero.id)


# --------------------------------------------------------------------------
# Crear usuario interno
# --------------------------------------------------------------------------


def test_crear_usuario_interno_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    correo_nuevo = f"nuevo-{uuid.uuid4().hex[:8]}@fashionstore.com"
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Juan Pérez",
                "correo": correo_nuevo,
                "password": "ClaveSegura123!",
                "rol": "ENCARGADO_SUCURSAL",
                "sucursal_id": sucursal.id,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["correo"] == correo_nuevo
        assert body["rol"] == "ENCARGADO_SUCURSAL"
        assert body["is_active"] is True
        assert body["sucursal"]["id"] == sucursal.id
        assert body["sucursal"]["ciudad"]["id"] == ciudad.id
        assert "password" not in body
        assert "password_hash" not in body
    finally:
        _delete_test_user(admin.id)
        creado = SessionLocal()
        try:
            existente = UsuariosRolesRepository(creado).get_by_correo(correo_nuevo)
            if existente:
                _delete_test_user(existente.id)
        finally:
            creado.close()
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


def test_crear_usuario_con_password_corta_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Password Corta",
                "correo": f"passcorta-{uuid.uuid4().hex[:8]}@fashionstore.com",
                "password": "1234567",
                "rol": "ENCARGADO_SUCURSAL",
                "sucursal_id": sucursal.id,
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


def test_crear_usuario_sin_sucursal_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Sin Sucursal",
                "correo": f"sinsucursal-{uuid.uuid4().hex[:8]}@fashionstore.com",
                "password": "ClaveSegura123!",
                "rol": "CAJERO",
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


def test_crear_usuario_con_sucursal_inexistente_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Sucursal Fantasma",
                "correo": f"sucursalfantasma-{uuid.uuid4().hex[:8]}@fashionstore.com",
                "password": "ClaveSegura123!",
                "rol": "CAJERO",
                "sucursal_id": 9_999_999,
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


def test_crear_usuario_con_correo_duplicado_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    existente = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Duplicado",
                "correo": existente.correo,
                "password": "ClaveSegura123!",
                "rol": "CAJERO",
                "sucursal_id": sucursal.id,
            },
        )
        assert response.status_code == 409
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(existente.id)
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


def test_crear_usuario_con_rol_cliente_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Cliente Intento",
                "correo": f"cliente-{uuid.uuid4().hex[:8]}@fashionstore.com",
                "password": "ClaveSegura123!",
                "rol": "CLIENTE",
                "sucursal_id": sucursal.id,
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


# --------------------------------------------------------------------------
# Editar datos básicos
# --------------------------------------------------------------------------


def test_editar_datos_basicos_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    objetivo = _create_test_user(RolUsuario.CAJERO, sucursal_id=sucursal.id)
    try:
        nuevo_correo = f"editado-{uuid.uuid4().hex[:8]}@fashionstore.com"
        response = client.put(
            f"/api/v1/usuarios/{objetivo.id}",
            headers=_auth_headers(admin),
            json={"nombre": "Nombre Editado", "correo": nuevo_correo, "sucursal_id": sucursal.id},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["nombre"] == "Nombre Editado"
        assert body["correo"] == nuevo_correo
        assert body["sucursal"]["id"] == sucursal.id
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(objetivo.id)
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


# --------------------------------------------------------------------------
# Cambiar rol
# --------------------------------------------------------------------------


def test_cambiar_rol_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    objetivo = _create_test_user(RolUsuario.CAJERO)
    try:
        response = client.patch(
            f"/api/v1/usuarios/{objetivo.id}/rol",
            headers=_auth_headers(admin),
            json={"rol": "ENCARGADO_SUCURSAL"},
        )
        assert response.status_code == 200
        assert response.json()["rol"] == "ENCARGADO_SUCURSAL"
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(objetivo.id)


def test_auto_cambiarse_el_rol_es_rechazado_por_proteccion_de_administrador():
    # El Administrador General ya no es alcanzable desde CU05 en absoluto (ver
    # sección "Protección del Administrador General"), así que este intento
    # falla con 404 antes de llegar a cualquier lógica de rol.
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.patch(
            f"/api/v1/usuarios/{admin.id}/rol",
            headers=_auth_headers(admin),
            json={"rol": "CAJERO"},
        )
        assert response.status_code == 404
    finally:
        _delete_test_user(admin.id)


# --------------------------------------------------------------------------
# Activar / desactivar
# --------------------------------------------------------------------------


def test_activar_desactivar_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    objetivo = _create_test_user(RolUsuario.CAJERO)
    try:
        desactivar = client.patch(
            f"/api/v1/usuarios/{objetivo.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert desactivar.status_code == 200
        assert desactivar.json()["is_active"] is False

        activar = client.patch(
            f"/api/v1/usuarios/{objetivo.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": True},
        )
        assert activar.status_code == 200
        assert activar.json()["is_active"] is True
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(objetivo.id)


def test_no_puede_desactivar_su_propia_cuenta():
    # El Administrador General queda protegido de forma general (404), lo cual
    # ya cubre el caso particular de auto-desactivación.
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.patch(
            f"/api/v1/usuarios/{admin.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        assert response.status_code == 404
    finally:
        _delete_test_user(admin.id)


def test_usuario_desactivado_no_puede_iniciar_sesion_luego_de_cu05():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    objetivo = _create_test_user(RolUsuario.CAJERO)
    try:
        client.patch(
            f"/api/v1/usuarios/{objetivo.id}/estado",
            headers=_auth_headers(admin),
            json={"is_active": False},
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"correo": objetivo.correo, "password": "ClaveSegura123!"},
        )
        assert login.status_code == 403
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(objetivo.id)


# --------------------------------------------------------------------------
# Vínculo con Proveedor (rol PROVEEDOR)
# --------------------------------------------------------------------------


def test_crear_usuario_proveedor_ok():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    proveedor = _create_test_proveedor()
    correo_nuevo = f"proveedor-{uuid.uuid4().hex[:8]}@fashionstore.com"
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Cuenta Proveedor",
                "correo": correo_nuevo,
                "password": "ClaveSegura123!",
                "rol": "PROVEEDOR",
                "proveedor_id": proveedor.id,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["rol"] == "PROVEEDOR"
        assert body["proveedor"]["id"] == proveedor.id
        assert body["sucursal"] is None
    finally:
        _delete_test_user(admin.id)
        creado = SessionLocal()
        try:
            existente = UsuariosRolesRepository(creado).get_by_correo(correo_nuevo)
            if existente:
                _delete_test_user(existente.id)
        finally:
            creado.close()
        _delete_test_proveedor(proveedor.id)


def test_crear_usuario_proveedor_sin_proveedor_id_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Sin Proveedor",
                "correo": f"sinproveedor-{uuid.uuid4().hex[:8]}@fashionstore.com",
                "password": "ClaveSegura123!",
                "rol": "PROVEEDOR",
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


def test_crear_usuario_proveedor_con_sucursal_id_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    proveedor = _create_test_proveedor()
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Proveedor Invalido",
                "correo": f"provinvalido-{uuid.uuid4().hex[:8]}@fashionstore.com",
                "password": "ClaveSegura123!",
                "rol": "PROVEEDOR",
                "proveedor_id": proveedor.id,
                "sucursal_id": sucursal.id,
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)
        _delete_test_proveedor(proveedor.id)
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


def test_crear_usuario_encargado_sin_sucursal_id_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    try:
        response = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Sin Sucursal",
                "correo": f"sinsucursal-{uuid.uuid4().hex[:8]}@fashionstore.com",
                "password": "ClaveSegura123!",
                "rol": "ENCARGADO_SUCURSAL",
            },
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)


def test_crear_dos_usuarios_para_el_mismo_proveedor_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    proveedor = _create_test_proveedor()
    primero = client.post(
        "/api/v1/usuarios",
        headers=_auth_headers(admin),
        json={
            "nombre": "Cuenta Uno",
            "correo": f"provuno-{uuid.uuid4().hex[:8]}@fashionstore.com",
            "password": "ClaveSegura123!",
            "rol": "PROVEEDOR",
            "proveedor_id": proveedor.id,
        },
    )
    try:
        segundo = client.post(
            "/api/v1/usuarios",
            headers=_auth_headers(admin),
            json={
                "nombre": "Cuenta Dos",
                "correo": f"provdos-{uuid.uuid4().hex[:8]}@fashionstore.com",
                "password": "ClaveSegura123!",
                "rol": "PROVEEDOR",
                "proveedor_id": proveedor.id,
            },
        )
        assert segundo.status_code == 409
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(primero.json()["id"])
        _delete_test_proveedor(proveedor.id)


def test_cambiar_rol_entre_grupo_sucursal_y_grupo_proveedor_es_rechazado():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    objetivo = _create_test_user(RolUsuario.CAJERO, sucursal_id=sucursal.id)
    try:
        response = client.patch(
            f"/api/v1/usuarios/{objetivo.id}/rol",
            headers=_auth_headers(admin),
            json={"rol": "PROVEEDOR"},
        )
        assert response.status_code == 422
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(objetivo.id)
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


# --------------------------------------------------------------------------
# Flujo completo: Administrador crea la cuenta -> CU01 la autentica
# --------------------------------------------------------------------------


def test_cuenta_encargado_creada_por_admin_puede_iniciar_sesion_por_cu01():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    correo = f"encargado-login-{uuid.uuid4().hex[:8]}@fashionstore.com"
    creado = client.post(
        "/api/v1/usuarios",
        headers=_auth_headers(admin),
        json={
            "nombre": "Encargado Login",
            "correo": correo,
            "password": "ClaveSegura123!",
            "rol": "ENCARGADO_SUCURSAL",
            "sucursal_id": sucursal.id,
        },
    )
    assert creado.status_code == 201
    try:
        login = client.post(
            "/api/v1/auth/login", json={"correo": correo, "password": "ClaveSegura123!"}
        )
        assert login.status_code == 200
        body = login.json()
        assert body["access_token"]
        assert body["usuario"]["rol"] == "ENCARGADO_SUCURSAL"
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(creado.json()["id"])
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


def test_cuenta_cajero_creada_por_admin_puede_iniciar_sesion_por_cu01():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    ciudad = _create_test_ciudad()
    sucursal = _create_test_sucursal(ciudad.id)
    correo = f"cajero-login-{uuid.uuid4().hex[:8]}@fashionstore.com"
    creado = client.post(
        "/api/v1/usuarios",
        headers=_auth_headers(admin),
        json={
            "nombre": "Cajero Login",
            "correo": correo,
            "password": "ClaveSegura123!",
            "rol": "CAJERO",
            "sucursal_id": sucursal.id,
        },
    )
    assert creado.status_code == 201
    try:
        login = client.post(
            "/api/v1/auth/login", json={"correo": correo, "password": "ClaveSegura123!"}
        )
        assert login.status_code == 200
        assert login.json()["usuario"]["rol"] == "CAJERO"
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(creado.json()["id"])
        _delete_test_sucursal(sucursal.id)
        _delete_test_ciudad(ciudad.id)


def test_cuenta_proveedor_creada_por_admin_puede_iniciar_sesion_por_cu01():
    admin = _create_test_user(RolUsuario.ADMINISTRADOR)
    proveedor = _create_test_proveedor()
    correo = f"proveedor-login-{uuid.uuid4().hex[:8]}@fashionstore.com"
    creado = client.post(
        "/api/v1/usuarios",
        headers=_auth_headers(admin),
        json={
            "nombre": "Proveedor Login",
            "correo": correo,
            "password": "ClaveSegura123!",
            "rol": "PROVEEDOR",
            "proveedor_id": proveedor.id,
        },
    )
    assert creado.status_code == 201
    try:
        login = client.post(
            "/api/v1/auth/login", json={"correo": correo, "password": "ClaveSegura123!"}
        )
        assert login.status_code == 200
        body = login.json()
        assert body["usuario"]["rol"] == "PROVEEDOR"
        assert set(body.keys()) == {"access_token", "token_type", "usuario"}
    finally:
        _delete_test_user(admin.id)
        _delete_test_user(creado.json()["id"])
        _delete_test_proveedor(proveedor.id)
