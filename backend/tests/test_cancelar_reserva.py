"""Pruebas de CU19 -- Cancelar reserva (Cliente).

Reutiliza el mismo escenario y helpers de CU17 (test_crear_reserva_prendas)
en vez de reconstruir producto/variante/sucursal/stock/cliente desde cero --
igual que ya hace test_consultar_reserva.py para CU18. Énfasis en: solo el
dueño puede cancelar, solo un detalle PENDIENTE/PREPARADA es cancelable, la
cancelación NUNCA borra la fila ni toca el stock físico (`cantidad`), solo
libera `stock_reservado` -- y esa unidad liberada vuelve a ser reservable
(CU17 sigue funcionando sobre el mismo stock).

Dos endpoints: cancelar UN detalle (`/reservas/detalles/{id}/cancelar`, no
afecta al resto de la reserva) y cancelar la reserva ENTERA
(`/reservas/{id}/cancelar`, cancela todos los detalles todavía cancelables).
El caso "cancelar una prenda libera solo su stock, sin afectar a las demás
prendas de la misma reserva" vive en test_reserva_multiples_prendas.py, que
arma ese escenario de varias prendas por reserva.
"""

from tests.test_crear_reserva_prendas import (
    _auth_headers,
    _create_test_user,
    _delete_test_user,
    _Escenario,
    _payload,
)
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P4_ReservasYAtencion.Models.reserva import EstadoReserva, Reserva, ReservaDetalle

client = TestClient(app)


def _crear_reserva(escenario: _Escenario, **overrides) -> dict:
    """Crea una reserva PENDIENTE vía el endpoint real de CU17 y devuelve el
    cuerpo completo (cabecera + detalles)."""
    respuesta = client.post(
        "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, **overrides)
    )
    assert respuesta.status_code == 201
    return respuesta.json()


def _forzar_estado_detalle(detalle_id: int, estado: EstadoReserva) -> None:
    db = SessionLocal()
    try:
        detalle = db.get(ReservaDetalle, detalle_id)
        detalle.estado = estado
        db.commit()
    finally:
        db.close()


# --------------------------------------------------------------------------
# Autorización
# --------------------------------------------------------------------------


def test_cancelar_sin_token_es_rechazada():
    response = client.patch("/api/v1/reservas/1/cancelar")
    assert response.status_code == 401


def test_cancelar_detalle_sin_token_es_rechazada():
    response = client.patch("/api/v1/reservas/detalles/1/cancelar")
    assert response.status_code == 401


def test_otro_cliente_no_puede_cancelar_una_reserva_ajena():
    escenario = _Escenario(stock_inicial=1)
    otro_cliente = _create_test_user(RolUsuario.CLIENTE)
    try:
        reserva = _crear_reserva(escenario, cantidad=1)

        response = client.patch(
            f"/api/v1/reservas/{reserva['id']}/cancelar", headers=_auth_headers(otro_cliente)
        )
        assert response.status_code == 404

        response_detalle = client.patch(
            f"/api/v1/reservas/detalles/{reserva['detalles'][0]['id']}/cancelar",
            headers=_auth_headers(otro_cliente),
        )
        assert response_detalle.status_code == 404

        # No debe haberse tocado ni la reserva ni el stock reservado.
        mias = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        assert mias[0]["estado_general"] == "PENDIENTE"
        assert escenario.stock_reservado_actual() == 1
    finally:
        _delete_test_user(otro_cliente.id)
        escenario.cleanup()


def test_encargado_no_puede_usar_el_endpoint_de_cliente():
    escenario = _Escenario(stock_inicial=1)
    encargado = _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal.id)
    try:
        reserva = _crear_reserva(escenario, cantidad=1)
        response = client.patch(
            f"/api/v1/reservas/{reserva['id']}/cancelar", headers=_auth_headers(encargado)
        )
        assert response.status_code == 403
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_cancelar_reserva_inexistente_devuelve_404():
    escenario = _Escenario()
    try:
        response = client.patch(
            "/api/v1/reservas/9999999/cancelar", headers=escenario.headers()
        )
        assert response.status_code == 404
    finally:
        escenario.cleanup()


def test_cancelar_detalle_inexistente_devuelve_404():
    escenario = _Escenario()
    try:
        response = client.patch(
            "/api/v1/reservas/detalles/9999999/cancelar", headers=escenario.headers()
        )
        assert response.status_code == 404
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Cancelación de la reserva completa -- estado, stock físico intacto
# --------------------------------------------------------------------------


def test_cliente_cancela_su_propia_reserva_pendiente():
    escenario = _Escenario(stock_inicial=1)
    try:
        reserva = _crear_reserva(escenario, cantidad=1)

        response = client.patch(
            f"/api/v1/reservas/{reserva['id']}/cancelar", headers=escenario.headers()
        )
        assert response.status_code == 200
        body = response.json()
        assert body["estado_general"] == "CANCELADA"
        assert body["id"] == reserva["id"]
        assert body["detalles"][0]["estado"] == "CANCELADA"
    finally:
        escenario.cleanup()


def test_cancelar_no_toca_stock_actual_y_libera_stock_reservado_en_exactamente_1():
    escenario = _Escenario(stock_inicial=5)
    try:
        reserva = _crear_reserva(escenario, cantidad=1)
        assert escenario.stock_reservado_actual() == 1

        client.patch(f"/api/v1/reservas/{reserva['id']}/cancelar", headers=escenario.headers())

        assert escenario.stock_actual() == 5  # stock físico NUNCA cambia.
        assert escenario.stock_reservado_actual() == 0  # se liberó exactamente 1.
    finally:
        escenario.cleanup()


def test_cancelar_libera_solo_la_cantidad_de_esa_reserva():
    escenario = _Escenario(stock_inicial=5)
    try:
        reserva = _crear_reserva(escenario, cantidad=2)
        assert escenario.stock_reservado_actual() == 2

        client.patch(f"/api/v1/reservas/{reserva['id']}/cancelar", headers=escenario.headers())

        assert escenario.stock_actual() == 5
        assert escenario.stock_reservado_actual() == 0
    finally:
        escenario.cleanup()


def test_cu18_muestra_el_nuevo_estado_cancelada():
    escenario = _Escenario(stock_inicial=1)
    try:
        reserva = _crear_reserva(escenario, cantidad=1)
        client.patch(f"/api/v1/reservas/{reserva['id']}/cancelar", headers=escenario.headers())

        mias = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        assert len(mias) == 1
        assert mias[0]["estado_general"] == "CANCELADA"
        assert mias[0]["detalles"][0]["estado"] == "CANCELADA"
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# Solo detalles PENDIENTE/PREPARADA son cancelables
# --------------------------------------------------------------------------


def test_una_reserva_ya_cancelada_no_puede_volver_a_cancelarse():
    escenario = _Escenario(stock_inicial=1)
    try:
        reserva = _crear_reserva(escenario, cantidad=1)
        primera = client.patch(
            f"/api/v1/reservas/{reserva['id']}/cancelar", headers=escenario.headers()
        )
        assert primera.status_code == 200
        assert escenario.stock_reservado_actual() == 0

        segunda = client.patch(
            f"/api/v1/reservas/{reserva['id']}/cancelar", headers=escenario.headers()
        )
        assert segunda.status_code == 422
        # No debe haber un segundo "descuento" (no puede quedar negativo, y
        # tampoco debe quedarse en -1 silenciosamente): el fallo de
        # validación no debe haber tocado stock_reservado en absoluto.
        assert escenario.stock_reservado_actual() == 0
    finally:
        escenario.cleanup()


def test_una_reserva_atendida_no_puede_cancelarse():
    escenario = _Escenario(stock_inicial=1)
    try:
        reserva = _crear_reserva(escenario, cantidad=1)
        _forzar_estado_detalle(reserva["detalles"][0]["id"], EstadoReserva.ATENDIDA)

        response = client.patch(
            f"/api/v1/reservas/{reserva['id']}/cancelar", headers=escenario.headers()
        )
        assert response.status_code == 422
        # ATENDIDA nunca libera stock_reservado por esta vía -- sigue en 1.
        assert escenario.stock_reservado_actual() == 1
    finally:
        escenario.cleanup()


def test_cancelar_un_detalle_ya_cancelado_es_rechazado():
    escenario = _Escenario(stock_inicial=1)
    try:
        reserva = _crear_reserva(escenario, cantidad=1)
        detalle_id = reserva["detalles"][0]["id"]

        primera = client.patch(f"/api/v1/reservas/detalles/{detalle_id}/cancelar", headers=escenario.headers())
        assert primera.status_code == 200

        segunda = client.patch(f"/api/v1/reservas/detalles/{detalle_id}/cancelar", headers=escenario.headers())
        assert segunda.status_code == 422
        assert escenario.stock_reservado_actual() == 0
    finally:
        escenario.cleanup()


# --------------------------------------------------------------------------
# La unidad liberada vuelve a estar disponible para CU17
# --------------------------------------------------------------------------


def test_tras_cancelar_cu17_puede_reservar_la_unidad_liberada():
    escenario = _Escenario(stock_inicial=1)
    try:
        primera_reserva = _crear_reserva(escenario, cantidad=1)

        # Con la única unidad ya reservada, una segunda reserva debe fallar.
        bloqueada = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=1)
        )
        assert bloqueada.status_code == 422

        cancelar = client.patch(
            f"/api/v1/reservas/{primera_reserva['id']}/cancelar", headers=escenario.headers()
        )
        assert cancelar.status_code == 200

        # Ahora sí debe poder reservarse de nuevo la misma unidad.
        nueva = client.post(
            "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, cantidad=1)
        )
        assert nueva.status_code == 201
        assert escenario.stock_reservado_actual() == 1
        assert escenario.stock_actual() == 1
    finally:
        escenario.cleanup()
