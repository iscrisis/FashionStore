"""Pruebas de CU07 - Consultar sucursales (público, sin login)."""

import uuid

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from modules.P1_SucursalesYCatalogos.Models.ciudad import Ciudad
from modules.P1_SucursalesYCatalogos.Models.sucursal import Sucursal

client = TestClient(app)


class _CiudadConSucursal:
    """Crea (y limpia) una ciudad activa con una sucursal activa -- para
    probar la consulta pública (CU07) sin depender de los endpoints
    administrativos de CU06."""

    def __init__(self, *, ciudad_activa: bool = True, sucursal_activa: bool = True):
        self.db = SessionLocal()
        sufijo = uuid.uuid4().hex[:8]

        self.ciudad = Ciudad(
            nombre=f"Ciudad {sufijo}", departamento="Santa Cruz", is_active=ciudad_activa
        )
        self.db.add(self.ciudad)
        self.db.commit()

        self.sucursal = Sucursal(
            nombre=f"Sucursal {sufijo}",
            ciudad_id=self.ciudad.id,
            direccion=f"Av. Siempre Viva {sufijo}",
            telefono="70012345",
            is_active=sucursal_activa,
        )
        self.db.add(self.sucursal)
        self.db.commit()
        self.db.refresh(self.sucursal)

    def cleanup(self) -> None:
        try:
            self.db.delete(self.sucursal)
            self.db.commit()
            self.db.delete(self.ciudad)
            self.db.commit()
        finally:
            self.db.close()


# --------------------------------------------------------------------------
# Acceso público (sin token)
# --------------------------------------------------------------------------


def test_listar_ciudades_no_requiere_login():
    response = client.get("/api/v1/sucursales-publicas/ciudades")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_listar_sucursales_no_requiere_login():
    response = client.get("/api/v1/sucursales-publicas/sucursales")
    assert response.status_code == 200


def test_obtener_sucursal_no_requiere_login():
    contexto = _CiudadConSucursal()
    try:
        response = client.get(f"/api/v1/sucursales-publicas/sucursales/{contexto.sucursal.id}")
        assert response.status_code == 200
    finally:
        contexto.cleanup()


# --------------------------------------------------------------------------
# Estructura de datos públicos
# --------------------------------------------------------------------------


def test_sucursal_publica_incluye_solo_datos_publicos():
    contexto = _CiudadConSucursal()
    try:
        response = client.get(f"/api/v1/sucursales-publicas/sucursales/{contexto.sucursal.id}")
        body = response.json()
        assert body["nombre"] == contexto.sucursal.nombre
        assert body["direccion"] == contexto.sucursal.direccion
        assert body["telefono"] == contexto.sucursal.telefono
        assert body["ciudad"]["id"] == contexto.ciudad.id
        assert body["ciudad"]["nombre"] == contexto.ciudad.nombre
        # Sin campos administrativos ni Departamento: el flujo público es
        # únicamente Ciudad -> Sucursal (ver sección 3 del caso de uso).
        assert "is_active" not in body
        assert "departamento" not in body["ciudad"]
    finally:
        contexto.cleanup()


def test_ciudad_publica_no_incluye_departamento():
    contexto = _CiudadConSucursal()
    try:
        response = client.get("/api/v1/sucursales-publicas/ciudades")
        ciudad = next(c for c in response.json() if c["id"] == contexto.ciudad.id)
        assert set(ciudad.keys()) == {"id", "nombre"}
    finally:
        contexto.cleanup()


# --------------------------------------------------------------------------
# Solo información activa/publicable
# --------------------------------------------------------------------------


def test_sucursal_inactiva_no_aparece_en_el_listado_ni_en_el_detalle():
    contexto = _CiudadConSucursal(sucursal_activa=False)
    try:
        listado = client.get("/api/v1/sucursales-publicas/sucursales")
        assert contexto.sucursal.id not in {s["id"] for s in listado.json()}

        detalle = client.get(f"/api/v1/sucursales-publicas/sucursales/{contexto.sucursal.id}")
        assert detalle.status_code == 404
    finally:
        contexto.cleanup()


def test_ciudad_inactiva_no_aparece_en_el_listado():
    contexto = _CiudadConSucursal(ciudad_activa=False)
    try:
        listado = client.get("/api/v1/sucursales-publicas/ciudades")
        assert contexto.ciudad.id not in {c["id"] for c in listado.json()}
    finally:
        contexto.cleanup()


def test_obtener_sucursal_inexistente_devuelve_404():
    response = client.get("/api/v1/sucursales-publicas/sucursales/9999999")
    assert response.status_code == 404


# --------------------------------------------------------------------------
# Filtro Ciudad -> Sucursal
# --------------------------------------------------------------------------


def test_filtrar_sucursales_por_ciudad():
    contexto_a = _CiudadConSucursal()
    contexto_b = _CiudadConSucursal()
    try:
        por_ciudad_a = client.get(
            f"/api/v1/sucursales-publicas/sucursales?ciudad_id={contexto_a.ciudad.id}"
        )
        ids = {s["id"] for s in por_ciudad_a.json()}
        assert contexto_a.sucursal.id in ids
        assert contexto_b.sucursal.id not in ids
    finally:
        contexto_a.cleanup()
        contexto_b.cleanup()
