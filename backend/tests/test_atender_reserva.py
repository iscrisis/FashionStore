"""Pruebas de CU20 -- Atender reserva de prendas (Encargado de Sucursal).

Reutiliza el mismo escenario y helpers de CU17 (test_crear_reserva_prendas)
en vez de reconstruir producto/variante/sucursal/stock/cliente desde cero, y
`_EscenarioMultiple`/`_reserva_con_varios_detalles` de
test_reserva_multiples_prendas.py para los casos que necesitan más de una
prenda por reserva.

Dos niveles de acción, NUNCA mezclados (ver CU20_AtenderReservaPrendas/
service.py):
  - a nivel RESERVA (`PATCH /reservas/{id}/confirmar-llegada` y
    `/finalizar-atencion`): un solo botón por reserva -- confirmar llegada
    NUNCA cambia el estado individual de ningún detalle; finalizar atención
    exige que todos los detalles activos ya tengan una decisión, libera el
    stock de los "no la compra" y deja la cabecera en LISTA_PARA_CAJA o
    ATENDIDA.
  - a nivel DETALLE (`PATCH /reservas/detalles/{id}/preparar` |
    `/no-la-compra` | `/enviar-a-caja`): preparar y decidir por prenda,
    individual -- "no la compra"/"enviar a caja" registran la decisión pero
    NO liberan/tocan stock todavía (eso ocurre recién al finalizar
    atención) ni aparecen al Cajero hasta que la reserva completa se cierre.

Énfasis en: la separación estricta de niveles, que ninguna transición de
CU20 toca stock físico (`cantidad`), que liberar stock_reservado ocurre
EXACTAMENTE una vez (al finalizar atención, o al vencer) incluso si se
repite la operación, que el panel agrupa por reserva, y la compatibilidad de
CU18/CU19 con el nuevo flujo.
"""

from datetime import datetime, timedelta, timezone

from tests.test_crear_reserva_prendas import (
    _auth_headers,
    _create_test_user,
    _delete_test_user,
    _Escenario,
    _payload,
)
from tests.test_reserva_multiples_prendas import _EscenarioMultiple, _reserva_con_varios_detalles
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P4_ReservasYAtencion.Models.reserva import Reserva

client = TestClient(app)


def _crear_reserva(escenario: _Escenario, **overrides) -> dict:
    """Crea una reserva PENDIENTE vía el endpoint real de CU17 y devuelve el
    cuerpo completo (cabecera + detalles)."""
    respuesta = client.post(
        "/api/v1/reservas", headers=escenario.headers(), json=_payload(escenario, **overrides)
    )
    assert respuesta.status_code == 201
    return respuesta.json()


def _crear_reserva_y_detalle_id(escenario: _Escenario, **overrides) -> tuple[int, int]:
    """Igual que _crear_reserva, pero devuelve (reserva_id, detalle_id) --
    conveniencia para los tests de este archivo, que en su mayoría actúan
    sobre un único detalle."""
    reserva = _crear_reserva(escenario, **overrides)
    return reserva["id"], reserva["detalles"][0]["id"]


def _encargado_de(escenario: _Escenario):
    return _create_test_user(RolUsuario.ENCARGADO_SUCURSAL, sucursal_id=escenario.sucursal.id)


def _cajero_de(escenario: _Escenario):
    return _create_test_user(RolUsuario.CAJERO, sucursal_id=escenario.sucursal.id)


def _forzar_bloque_vencido(reserva_id: int) -> None:
    """Retrocede fecha_reserva/hora_inicio de una reserva ya creada (la
    CABECERA -- el bloque horario es compartido por todos sus detalles) a un
    bloque que terminó hace 2 horas -- no se puede lograr esto vía el
    endpoint real de CU17 (rechaza fechas/horas pasadas), así que se
    manipula directo en la base."""
    db = SessionLocal()
    try:
        reserva = db.get(Reserva, reserva_id)
        hace_2h = datetime.now(timezone.utc) - timedelta(hours=2)
        reserva.fecha_reserva = hace_2h.date()
        reserva.hora_inicio = hace_2h.time().replace(minute=0, second=0, microsecond=0)
        db.commit()
    finally:
        db.close()


def _preparar(detalle_id: int, encargado):
    return client.patch(f"/api/v1/reservas/detalles/{detalle_id}/preparar", headers=_auth_headers(encargado))


def _confirmar_llegada(reserva_id: int, encargado):
    return client.patch(f"/api/v1/reservas/{reserva_id}/confirmar-llegada", headers=_auth_headers(encargado))


def _no_la_compra(detalle_id: int, encargado):
    return client.patch(f"/api/v1/reservas/detalles/{detalle_id}/no-la-compra", headers=_auth_headers(encargado))


def _enviar_a_caja(detalle_id: int, encargado):
    return client.patch(f"/api/v1/reservas/detalles/{detalle_id}/enviar-a-caja", headers=_auth_headers(encargado))


def _finalizar_atencion(reserva_id: int, encargado):
    return client.patch(f"/api/v1/reservas/{reserva_id}/finalizar-atencion", headers=_auth_headers(encargado))


# --------------------------------------------------------------------------
# Aislamiento por sucursal y seguridad
# --------------------------------------------------------------------------


def test_encargado_solo_ve_reservas_de_su_sucursal():
    escenario_a = _Escenario(stock_inicial=5)
    escenario_b = _Escenario(stock_inicial=5)
    encargado_a = _encargado_de(escenario_a)
    try:
        reserva_a = _crear_reserva(escenario_a)
        _crear_reserva(escenario_b)

        respuesta = client.get("/api/v1/reservas/panel", headers=_auth_headers(encargado_a))
        assert respuesta.status_code == 200
        ids = {fila["id"] for fila in respuesta.json()}
        assert ids == {reserva_a["id"]}
    finally:
        _delete_test_user(encargado_a.id)
        escenario_a.cleanup()
        escenario_b.cleanup()


def test_panel_sin_token_es_rechazado():
    response = client.get("/api/v1/reservas/panel")
    assert response.status_code == 401


def test_cliente_no_puede_usar_el_panel_del_encargado():
    escenario = _Escenario()
    try:
        response = client.get("/api/v1/reservas/panel", headers=escenario.headers())
        assert response.status_code == 403
    finally:
        escenario.cleanup()


def test_cliente_no_puede_usar_endpoints_internos_de_cu20():
    escenario = _Escenario(stock_inicial=5)
    try:
        _, detalle_id = _crear_reserva_y_detalle_id(escenario)
        response = client.patch(
            f"/api/v1/reservas/detalles/{detalle_id}/preparar", headers=escenario.headers()
        )
        assert response.status_code == 403
    finally:
        escenario.cleanup()


# 15. Otro encargado/sucursal no puede operar la reserva -- a nivel detalle
# Y a nivel cabecera.
def test_otro_encargado_de_otra_sucursal_no_puede_preparar():
    escenario_a = _Escenario(stock_inicial=5)
    escenario_b = _Escenario(stock_inicial=5)
    encargado_b = _encargado_de(escenario_b)
    try:
        _, detalle_a = _crear_reserva_y_detalle_id(escenario_a)

        response = _preparar(detalle_a, encargado_b)
        assert response.status_code == 404
        assert escenario_a.stock_reservado_actual() == 1
    finally:
        _delete_test_user(encargado_b.id)
        escenario_a.cleanup()
        escenario_b.cleanup()


def test_otro_encargado_de_otra_sucursal_no_puede_confirmar_llegada():
    escenario_a = _Escenario(stock_inicial=5)
    escenario_b = _Escenario(stock_inicial=5)
    encargado_b = _encargado_de(escenario_b)
    try:
        reserva_a, _ = _crear_reserva_y_detalle_id(escenario_a)

        response = _confirmar_llegada(reserva_a, encargado_b)
        assert response.status_code == 404
    finally:
        _delete_test_user(encargado_b.id)
        escenario_a.cleanup()
        escenario_b.cleanup()


def test_otro_encargado_de_otra_sucursal_no_puede_finalizar_atencion():
    escenario_a = _Escenario(stock_inicial=5)
    escenario_b = _Escenario(stock_inicial=5)
    encargado_a = _encargado_de(escenario_a)
    encargado_b = _encargado_de(escenario_b)
    try:
        reserva_a, detalle_a = _crear_reserva_y_detalle_id(escenario_a)
        _preparar(detalle_a, encargado_a)
        _confirmar_llegada(reserva_a, encargado_a)
        _no_la_compra(detalle_a, encargado_a)

        response = _finalizar_atencion(reserva_a, encargado_b)
        assert response.status_code == 404
        # No debe haberse liberado el stock -- la operación fue rechazada.
        assert escenario_a.stock_reservado_actual() == 1
    finally:
        _delete_test_user(encargado_a.id)
        _delete_test_user(encargado_b.id)
        escenario_a.cleanup()
        escenario_b.cleanup()


# --------------------------------------------------------------------------
# Panel agrupado -- una tarjeta por reserva, con sus detalles anidados
# --------------------------------------------------------------------------


def test_panel_agrupa_por_reserva_con_cliente_y_detalles_anidados():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva = _crear_reserva(escenario, cantidad=2)

        respuesta = client.get("/api/v1/reservas/panel", headers=_auth_headers(encargado))
        assert respuesta.status_code == 200
        fila = next(f for f in respuesta.json() if f["id"] == reserva["id"])

        assert fila["codigo_reserva"] == reserva["codigo_reserva"]
        assert fila["cliente"]["nombre"] == escenario.cliente.nombre
        assert fila["estado_general"] == "PENDIENTE"
        assert len(fila["detalles"]) == 1
        assert fila["detalles"][0]["cantidad"] == 2
        assert fila["detalles"][0]["estado"] == "PENDIENTE"
        assert fila["detalles"][0]["producto"]["nombre"] == escenario.producto.nombre
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 1/2. Reserva con 2+ detalles -- preparar una prenda no afecta a las demás.
# --------------------------------------------------------------------------


def test_reserva_con_dos_o_mas_detalles():
    escenario = _EscenarioMultiple(n_prendas_extra=2)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        assert len(reserva.detalles) == 3
    finally:
        escenario.cleanup()


def test_preparar_prenda_a_no_afecta_prenda_b():
    escenario = _EscenarioMultiple(n_prendas_extra=1, stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        prenda_a, prenda_b = reserva.detalles

        respuesta = _preparar(prenda_a.id, encargado)
        assert respuesta.status_code == 200
        assert respuesta.json()["estado"] == "PREPARADA"

        panel = client.get("/api/v1/reservas/panel", headers=_auth_headers(encargado)).json()
        fila = next(f for f in panel if f["id"] == reserva.id)
        estados = {d["id"]: d["estado"] for d in fila["detalles"]}
        assert estados[prenda_a.id] == "PREPARADA"
        assert estados[prenda_b.id] == "PENDIENTE"  # intacta.
        # Ninguna transición de preparar toca stock (punto 13).
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[0]) == 1
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 1
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 3/4. Confirmar llegada: un solo botón por CABECERA, nunca cambia el
# estado individual de los detalles.
# --------------------------------------------------------------------------


def test_confirmar_llegada_ya_no_existe_a_nivel_detalle():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        _, detalle_id = _crear_reserva_y_detalle_id(escenario)
        response = client.patch(
            f"/api/v1/reservas/detalles/{detalle_id}/confirmar-llegada", headers=_auth_headers(encargado)
        )
        # La ruta ya no existe -- ningún router de CU20 la registra.
        assert response.status_code == 404
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_confirmar_llegada_reserva_no_cambia_automaticamente_estados_de_detalles():
    escenario = _EscenarioMultiple(n_prendas_extra=1, stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        prenda_a, prenda_b = reserva.detalles
        _preparar(prenda_a.id, encargado)
        _preparar(prenda_b.id, encargado)

        respuesta = _confirmar_llegada(reserva.id, encargado)
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["estado_general"] == "EN_ATENCION"

        # Los detalles conservan exactamente el estado que tenían -- ninguno
        # pasa a EN_ATENCION automáticamente.
        estados = {d["id"]: d["estado"] for d in cuerpo["detalles"]}
        assert estados[prenda_a.id] == "PREPARADA"
        assert estados[prenda_b.id] == "PREPARADA"
        # No modifica stock.
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[0]) == 1
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 1
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_confirmar_llegada_solo_permitida_desde_pendiente_o_preparada():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva_id, detalle_id = _crear_reserva_y_detalle_id(escenario)
        _confirmar_llegada(reserva_id, encargado)

        segunda = _confirmar_llegada(reserva_id, encargado)
        assert segunda.status_code == 422
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 5/13. Decisiones por prenda -- no la compra / enviar a caja. Ninguna toca
# stock_actual; "no la compra" NO libera stock_reservado todavía (eso
# ocurre recién al finalizar atención).
# --------------------------------------------------------------------------


def test_decisiones_requieren_reserva_en_atencion_y_detalle_preparado():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        _, detalle_id = _crear_reserva_y_detalle_id(escenario)
        # Reserva todavía PENDIENTE (no se confirmó llegada) -- rechazado.
        assert _no_la_compra(detalle_id, encargado).status_code == 422
        assert _enviar_a_caja(detalle_id, encargado).status_code == 422
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_no_la_compra_no_libera_stock_de_inmediato_solo_al_finalizar():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva_id, detalle_id = _crear_reserva_y_detalle_id(escenario)
        _preparar(detalle_id, encargado)
        _confirmar_llegada(reserva_id, encargado)

        respuesta = _no_la_compra(detalle_id, encargado)
        assert respuesta.status_code == 200
        assert respuesta.json()["estado"] == "ATENDIDA"
        # Decisión persistida, pero SIN liberar stock todavía.
        assert escenario.stock_reservado_actual() == 1
        assert escenario.stock_actual() == 5

        _finalizar_atencion(reserva_id, encargado)
        # Recién ahora se libera.
        assert escenario.stock_reservado_actual() == 0
        assert escenario.stock_actual() == 5
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_enviar_a_caja_mantiene_stock_reservado():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva_id, detalle_id = _crear_reserva_y_detalle_id(escenario)
        _preparar(detalle_id, encargado)
        _confirmar_llegada(reserva_id, encargado)

        respuesta = _enviar_a_caja(detalle_id, encargado)
        assert respuesta.status_code == 200
        assert respuesta.json()["estado"] == "LISTA_PARA_CAJA"
        assert escenario.stock_reservado_actual() == 1
        assert escenario.stock_actual() == 5
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 7/8. Finalizar atención -- rechazado con decisiones pendientes, aceptado
# cuando todas están resueltas.
# --------------------------------------------------------------------------


def test_finalizar_atencion_rechazado_si_hay_detalle_sin_decision():
    escenario = _EscenarioMultiple(n_prendas_extra=1, stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        prenda_a, prenda_b = reserva.detalles
        _preparar(prenda_a.id, encargado)
        _preparar(prenda_b.id, encargado)
        _confirmar_llegada(reserva.id, encargado)
        _no_la_compra(prenda_a.id, encargado)
        # prenda_b sigue PREPARADA, sin decisión.

        respuesta = _finalizar_atencion(reserva.id, encargado)
        assert respuesta.status_code == 422
        # No debe haber liberado nada todavía.
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[0]) == 1
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 1
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_finalizar_atencion_se_habilita_cuando_todas_las_prendas_tienen_decision():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva_id, detalle_id = _crear_reserva_y_detalle_id(escenario)
        _preparar(detalle_id, encargado)
        _confirmar_llegada(reserva_id, encargado)
        _enviar_a_caja(detalle_id, encargado)

        respuesta = _finalizar_atencion(reserva_id, encargado)
        assert respuesta.status_code == 200
        assert respuesta.json()["estado_general"] == "LISTA_PARA_CAJA"
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 9/10/11. Caso mixto -- A y C a caja, B no compra.
# --------------------------------------------------------------------------


def test_caso_mixto_finalizar_deja_cabecera_lista_para_caja_y_libera_solo_b():
    escenario = _EscenarioMultiple(n_prendas_extra=2, stock_inicial=5)
    encargado = _encargado_de(escenario)
    cajero = _cajero_de(escenario)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        a, b, c = reserva.detalles
        for detalle in (a, b, c):
            _preparar(detalle.id, encargado)
        _confirmar_llegada(reserva.id, encargado)

        _enviar_a_caja(a.id, encargado)
        _no_la_compra(b.id, encargado)
        # Todavía falta decidir C -- ni siquiera debería llegar al cajero.
        cajero_antes = client.get("/api/v1/reservas/cajero/pendientes", headers=_auth_headers(cajero)).json()
        assert cajero_antes == []  # punto 6: nada al cajero mientras falte una decisión.

        _enviar_a_caja(c.id, encargado)

        respuesta = _finalizar_atencion(reserva.id, encargado)
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["estado_general"] == "LISTA_PARA_CAJA"
        estados = {d["id"]: d["estado"] for d in cuerpo["detalles"]}
        assert estados[a.id] == "LISTA_PARA_CAJA"
        assert estados[b.id] == "ATENDIDA"
        assert estados[c.id] == "LISTA_PARA_CAJA"

        # A y C mantienen su stock_reservado; B liberó el suyo.
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[0]) == 1
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 0
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[2]) == 1
        # El físico nunca cambia (punto 13).
        assert escenario.stock_actual() == 5

        # 10/11: el cajero ve UNA sola reserva con A y C juntas -- B nunca aparece.
        cajero_despues = client.get("/api/v1/reservas/cajero/pendientes", headers=_auth_headers(cajero)).json()
        assert len(cajero_despues) == 1
        fila = cajero_despues[0]
        assert fila["id"] == reserva.id
        assert fila["estado_general"] == "LISTA_PARA_CAJA"
        detalles_cajero = {d["id"] for d in fila["detalles"]}
        assert detalles_cajero == {a.id, c.id}
    finally:
        _delete_test_user(cajero.id)
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 12. Caso todas "no la compra" -- cabecera ATENDIDA, nada al cajero.
# --------------------------------------------------------------------------


def test_caso_ninguna_prenda_comprada_cabecera_queda_atendida():
    escenario = _EscenarioMultiple(n_prendas_extra=1, stock_inicial=5)
    encargado = _encargado_de(escenario)
    cajero = _cajero_de(escenario)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        a, b = reserva.detalles
        _preparar(a.id, encargado)
        _preparar(b.id, encargado)
        _confirmar_llegada(reserva.id, encargado)
        _no_la_compra(a.id, encargado)
        _no_la_compra(b.id, encargado)

        respuesta = _finalizar_atencion(reserva.id, encargado)
        assert respuesta.status_code == 200
        assert respuesta.json()["estado_general"] == "ATENDIDA"

        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[0]) == 0
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 0
        assert escenario.stock_actual() == 5

        cajero_despues = client.get("/api/v1/reservas/cajero/pendientes", headers=_auth_headers(cajero)).json()
        assert cajero_despues == []
    finally:
        _delete_test_user(cajero.id)
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# 14. Repetir FINALIZAR ATENCIÓN no libera stock dos veces.
# --------------------------------------------------------------------------


def test_repetir_finalizar_atencion_no_duplica_la_liberacion():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva_id, detalle_id = _crear_reserva_y_detalle_id(escenario)
        _preparar(detalle_id, encargado)
        _confirmar_llegada(reserva_id, encargado)
        _no_la_compra(detalle_id, encargado)

        primera = _finalizar_atencion(reserva_id, encargado)
        assert primera.status_code == 200
        assert escenario.stock_reservado_actual() == 0

        segunda = _finalizar_atencion(reserva_id, encargado)
        assert segunda.status_code == 422
        assert escenario.stock_reservado_actual() == 0
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# Vencimiento reactivo -- nunca vence EN_ATENCION en adelante, ni una prenda
# todavía PREPARADA si su cabecera ya llegó.
# --------------------------------------------------------------------------


def test_reserva_pendiente_vencida_libera_stock_al_consultar_el_panel():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva_id, _ = _crear_reserva_y_detalle_id(escenario, cantidad=1)
        _forzar_bloque_vencido(reserva_id)
        assert escenario.stock_reservado_actual() == 1

        respuesta = client.get("/api/v1/reservas/panel", headers=_auth_headers(encargado))
        assert respuesta.status_code == 200
        fila = next(f for f in respuesta.json() if f["id"] == reserva_id)
        assert fila["estado_general"] == "VENCIDA"
        assert fila["detalles"][0]["estado"] == "VENCIDA"
        assert escenario.stock_actual() == 5
        assert escenario.stock_reservado_actual() == 0
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_reserva_vencida_se_libera_una_sola_vez_aunque_se_consulte_dos_veces():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva_id, _ = _crear_reserva_y_detalle_id(escenario, cantidad=1)
        _forzar_bloque_vencido(reserva_id)

        client.get("/api/v1/reservas/panel", headers=_auth_headers(encargado))
        assert escenario.stock_reservado_actual() == 0

        client.get("/api/v1/reservas/panel", headers=_auth_headers(encargado))
        assert escenario.stock_reservado_actual() == 0
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_confirmar_llegada_de_reserva_ya_vencida_es_rechazada():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva_id, _ = _crear_reserva_y_detalle_id(escenario, cantidad=1)
        _forzar_bloque_vencido(reserva_id)

        respuesta = _confirmar_llegada(reserva_id, encargado)
        assert respuesta.status_code == 422
        assert escenario.stock_reservado_actual() == 0
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_prenda_preparada_no_vence_si_su_reserva_ya_esta_en_atencion():
    """Un detalle todavía PREPARADA (sin decisión) es, en sí mismo, un
    estado "vencible" -- pero si su CABECERA ya está EN_ATENCION (el
    Cliente llegó), esa prenda nunca debe vencer aunque el bloque horario ya
    haya terminado."""
    escenario = _EscenarioMultiple(n_prendas_extra=1, stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        prenda_a, prenda_b = reserva.detalles
        _preparar(prenda_a.id, encargado)
        # prenda_b se deja PENDIENTE a propósito -- solo importa que la
        # CABECERA ya esté EN_ATENCION.
        _confirmar_llegada(reserva.id, encargado)
        _forzar_bloque_vencido(reserva.id)

        panel = client.get("/api/v1/reservas/panel", headers=_auth_headers(encargado)).json()
        fila = next(f for f in panel if f["id"] == reserva.id)
        assert fila["estado_general"] == "EN_ATENCION"
        estados = {d["id"]: d["estado"] for d in fila["detalles"]}
        assert estados[prenda_a.id] == "PREPARADA"
        assert estados[prenda_b.id] == "PENDIENTE"
        # Ninguna liberó stock -- ninguna venció.
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[0]) == 1
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 1
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# Integración con CU18 (Mis reservas) y CU19 (Cancelar reserva)
# --------------------------------------------------------------------------


def test_cu18_refleja_los_nuevos_estados_de_cu20():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        _, detalle_id = _crear_reserva_y_detalle_id(escenario, cantidad=1)
        _preparar(detalle_id, encargado)

        mias = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        assert mias[0]["estado_general"] == "PREPARADA"
        assert mias[0]["detalles"][0]["estado"] == "PREPARADA"
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_cu18_muestra_en_atencion_tras_confirmar_llegada():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva_id, detalle_id = _crear_reserva_y_detalle_id(escenario, cantidad=1)
        _preparar(detalle_id, encargado)
        _confirmar_llegada(reserva_id, encargado)

        mias = client.get("/api/v1/reservas/mias", headers=escenario.headers()).json()
        assert mias[0]["estado_general"] == "EN_ATENCION"
        # El detalle sigue PREPARADA -- CU18 nunca lo muestra "EN_ATENCION"
        # por sí mismo (ese estado ya no existe a nivel detalle).
        assert mias[0]["detalles"][0]["estado"] == "PREPARADA"
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_cu19_permite_cancelar_una_reserva_preparada():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva_id, detalle_id = _crear_reserva_y_detalle_id(escenario, cantidad=1)
        _preparar(detalle_id, encargado)

        response = client.patch(
            f"/api/v1/reservas/{reserva_id}/cancelar", headers=escenario.headers()
        )
        assert response.status_code == 200
        assert response.json()["estado_general"] == "CANCELADA"
        assert escenario.stock_reservado_actual() == 0
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_cu19_puede_cancelar_un_detalle_todavia_preparada_aunque_la_reserva_ya_este_en_atencion():
    """La llegada es de la RESERVA, no de cada prenda -- un detalle que
    sigue PREPARADA (sin decisión) conserva su propio estado cancelable
    aunque la cabecera ya esté EN_ATENCION (otro detalle de la misma reserva
    puede estar más avanzado)."""
    escenario = _EscenarioMultiple(n_prendas_extra=1, stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        reserva = _reserva_con_varios_detalles(escenario)
        prenda_a, prenda_b = reserva.detalles
        _preparar(prenda_a.id, encargado)
        _preparar(prenda_b.id, encargado)
        _confirmar_llegada(reserva.id, encargado)

        # prenda_b sigue PREPARADA (sin decisión) -- el Cliente puede
        # todavía cancelarla vía CU19.
        headers_cliente = escenario.headers()
        response = client.patch(f"/api/v1/reservas/detalles/{prenda_b.id}/cancelar", headers=headers_cliente)
        assert response.status_code == 200
        assert response.json()["estado"] == "CANCELADA"
        assert escenario.stock_reservado_de(escenario.todas_las_variantes()[1]) == 0

        # La cabecera sigue EN_ATENCION -- CU19 no debe haberla "regresado".
        panel = client.get("/api/v1/reservas/panel", headers=_auth_headers(encargado)).json()
        fila = next(f for f in panel if f["id"] == reserva.id)
        assert fila["estado_general"] == "EN_ATENCION"
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


# --------------------------------------------------------------------------
# Integración mínima con Cajero -- GET /reservas/cajero/pendientes
# --------------------------------------------------------------------------


def test_pendientes_cajero_sin_token_es_rechazado():
    response = client.get("/api/v1/reservas/cajero/pendientes")
    assert response.status_code == 401


def test_encargado_no_puede_usar_el_endpoint_del_cajero():
    escenario = _Escenario(stock_inicial=5)
    encargado = _encargado_de(escenario)
    try:
        response = client.get(
            "/api/v1/reservas/cajero/pendientes", headers=_auth_headers(encargado)
        )
        assert response.status_code == 403
    finally:
        _delete_test_user(encargado.id)
        escenario.cleanup()


def test_cliente_no_puede_usar_el_endpoint_del_cajero():
    escenario = _Escenario(stock_inicial=5)
    try:
        response = client.get(
            "/api/v1/reservas/cajero/pendientes", headers=escenario.headers()
        )
        assert response.status_code == 403
    finally:
        escenario.cleanup()


def test_cajero_de_otra_sucursal_no_ve_la_reserva():
    escenario_a = _Escenario(stock_inicial=5)
    escenario_b = _Escenario(stock_inicial=5)
    encargado_a = _encargado_de(escenario_a)
    cajero_b = _cajero_de(escenario_b)
    try:
        reserva_id, detalle_id = _crear_reserva_y_detalle_id(escenario_a)
        _preparar(detalle_id, encargado_a)
        _confirmar_llegada(reserva_id, encargado_a)
        _enviar_a_caja(detalle_id, encargado_a)
        _finalizar_atencion(reserva_id, encargado_a)

        cuerpo = client.get(
            "/api/v1/reservas/cajero/pendientes", headers=_auth_headers(cajero_b)
        ).json()
        assert cuerpo == []
    finally:
        _delete_test_user(cajero_b.id)
        _delete_test_user(encargado_a.id)
        escenario_a.cleanup()
        escenario_b.cleanup()
