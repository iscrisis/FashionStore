"""CU18 -- Consultar reserva (Cliente).

El Cliente autenticado consulta sus propias reservas (solo lectura, sin
acciones de confirmar/cancelar/atender -- eso queda fuera de este alcance).

No hay router/service/repository propios en este paquete: CU17 ya expone
`GET /reservas/mias` (ver CU17_CrearReservaPrendas/router.py) con exactamente
el contrato que CU18 necesita -- cliente_id resuelto SIEMPRE del usuario
autenticado, nunca de la URL, y una reserva por Cliente jamás visible para
otro. Crear un segundo endpoint aquí sería duplicar esa misma lógica de
autorización y de lectura sin ningún beneficio.

`ReservaOut` (ver CU17_CrearReservaPrendas/schemas.py) es la cabecera de una
reserva (una visita del Cliente a una sucursal, en un bloque horario) con
TODAS sus prendas anidadas en `detalles` -- una tarjeta por reserva, nunca
una por prenda (ver Models/reserva.py). Lo que CU18 agregó sobre lo que ya
tenía CU17:
  - `SucursalResumen.ciudad` (id, nombre) -- la tarjeta muestra sucursal Y
    ciudad; Sucursal.ciudad ya viene cargada (relationship lazy="joined"),
    no agrega ninguna consulta nueva.
  - `ReservaOut.hora_fin` -- el bloque reservado siempre dura 1h exacta (ver
    P4_ReservasYAtencion/Models/reserva.py), se calcula en
    CU17_CrearReservaPrendas/service.py a partir de hora_inicio.
  - `ReservaOut.codigo_reserva`/`estado_general` y `detalles[].estado` --
    identificador visible (ej. "RS-00025") y estado agregado de la reserva,
    más el estado individual de cada prenda dentro de ella.

La traducción de cada `estado` (PENDIENTE/CANCELADA/ATENDIDA/...) a un texto
amable para el Cliente ("Pendiente de atención", "Atendida", "Cancelada") es
un detalle de presentación: vive en el frontend (Angular), no en este
contrato -- el backend sigue devolviendo el enum real, igual que el resto de
la API.
"""
