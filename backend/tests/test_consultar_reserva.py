"""Pruebas de CU18 -- Consultar reserva (Cliente).

Reutiliza el mismo escenario y helpers de CU17 (test_crear_reserva_prendas)
en vez de reconstruir producto/variante/sucursal/stock/cliente desde cero --
CU18 no agrega ningún endpoint nuevo, solo enriquece la respuesta de
GET /reservas/mias que CU17 ya expone (ver CU18_ConsultarReserva/__init__.py).
Este archivo se enfoca en lo que CU18 agrega: el aislamiento por cliente ya
probado en CU17 y, sobre todo, el contrato agrupado -- una tarjeta por
RESERVA (cabecera: código, sucursal+ciudad, fecha, horario, estado_general),
con sus prendas anidadas en `detalles` (producto+imagen, variante talla/
color, cantidad, estado individual) -- nunca una fila por prenda.

Los casos con más de un detalle por reserva (una visita con varias prendas)
viven en test_reserva_multiples_prendas.py, que construye ese escenario
directo contra el modelo (CU17 todavía no expone un carrito, ver CU21).
"""

from tests.test_crear_reserva_prendas import (
    _auth_headers,
    _create_test_user,
    _delete_test_user,
    _Escenario,
    _payload,
)
from fastapi.testclient import TestClient

from app.main import app
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario

client = TestClient(app)


def test_cliente_autenticado_consulta_sus_reservas():
    escenario = _Escenario(stock_inicial=5)
    try:
        client.post("/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario))
        response = client.get("/api/v1/reservas/mias", headers=escenario.headers())
        assert response.status_code == 200
        assert len(response.json()) == 1
    finally:
        escenario.cleanup()


def test_cliente_obtiene_unicamente_las_suyas():
    escenario_a = _Escenario(stock_inicial=5)
    escenario_b = _Escenario(stock_inicial=5)
    try:
        client.post("/api/v1/reservas", headers=escenario_a.headers(), json=_payload(escenario_a))
        client.post("/api/v1/reservas", headers=escenario_b.headers(), json=_payload(escenario_b))

        mias_a = client.get("/api/v1/reservas/mias", headers=escenario_a.headers()).json()
        mias_b = client.get("/api/v1/reservas/mias", headers=escenario_b.headers()).json()

        assert len(mias_a) == 1
        assert len(mias_b) == 1
        assert mias_a[0]["sucursal"]["id"] == escenario_a.sucursal.id
        assert mias_b[0]["sucursal"]["id"] == escenario_b.sucursal.id
    finally:
        escenario_a.cleanup()
        escenario_b.cleanup()


def test_otro_cliente_no_puede_consultar_reservas_ajenas():
    escenario_a = _Escenario(stock_inicial=5)
    escenario_b = _Escenario(stock_inicial=5)
    try:
        client.post("/api/v1/reservas", headers=escenario_a.headers(), json=_payload(escenario_a))
        mias_b = client.get("/api/v1/reservas/mias", headers=escenario_b.headers()).json()
        assert mias_b == []
    finally:
        escenario_a.cleanup()
        escenario_b.cleanup()


def test_usuario_sin_autenticar_no_puede_consultar_reservas():
    response = client.get("/api/v1/reservas/mias")
    assert response.status_code == 401


def test_encargado_no_puede_usar_el_endpoint_de_cliente():
    escenario = _Escenario()
    encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal.id)
    try:
        response = client.get("/api/v1/reservas/mias", headers=_auth_headers(encargado))
        assert response.status_code == 403
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_cliente_sin_reservas_devuelve_coleccion_vacia():
    escenario = _Escenario(stock_inicial=5)
    try:
        response = client.get("/api/v1/reservas/mias", headers=escenario.headers())
        assert response.status_code == 200
        assert response.json() == []
    finally:
        escenario.cleanup()


def test_reserva_incluye_todos_los_datos_que_necesita_la_tarjeta_del_cliente():
    escenario = _Escenario(stock_inicial=5)
    try:
        crear = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=2)
        )
        assert crear.status_code == 201

        response = client.get("/api/v1/reservas/mias", headers=escenario.headers())
        assert response.status_code == 200
        reserva = response.json()[0]

        # Cabecera: código visible, sucursal + ciudad, fecha, horario, estado
        # agregado.
        assert reserva["codigo_reserva"].startswith("RS-")
        assert reserva["sucursal"]["nombre"] == escenario.sucursal.nombre
        assert reserva["sucursal"]["ciudad"]["nombre"] == escenario.ciudad.nombre
        assert reserva["fecha_reserva"]
        assert reserva["hora_inicio"]
        assert reserva["hora_fin"]
        assert reserva["estado_general"] == "PENDIENTE"

        # Detalle: producto + imagen, variante talla/color, cantidad, estado.
        assert len(reserva["detalles"]) == 1
        detalle = reserva["detalles"][0]
        assert detalle["producto"]["nombre"] == escenario.producto.nombre
        assert "imagen_principal_url" in detalle["producto"]
        assert detalle["variante"]["talla"]["nombre"] == escenario.talla.nombre
        assert detalle["variante"]["color"]["nombre"] == escenario.color.nombre
        assert detalle["cantidad"] == 2
        assert detalle["estado"] == "PENDIENTE"
    finally:
        escenario.cleanup()
