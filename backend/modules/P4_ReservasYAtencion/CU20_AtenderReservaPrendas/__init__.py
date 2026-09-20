"""CU20 -- Atender reserva de prendas (Encargado de Sucursal, más una
integración mínima de solo lectura para Cajero).

El ENCARGADO_SUCURSAL autenticado consulta y avanza el estado de las
reservas de SU propia sucursal (resuelta siempre de `actor.sucursal_id`,
igual que CU14/CU15/CU16 -- nunca de un id que Angular pueda manipular; la
sucursal vive en la CABECERA de la reserva, ver Models/reserva.py). Cada
acción opera sobre UN ReservaDetalle (una prenda dentro de una reserva), no
sobre la reserva completa -- el panel (GET /reservas/panel) sigue mostrando
la vista agrupada: una tarjeta por reserva, con todas sus prendas anidadas.

El CAJERO autenticado (misma sucursal, mismo `actor.sucursal_id`) solo
CONSULTA -- GET /reservas/cajero/pendientes -- los detalles que el Encargado
ya dejó en LISTA_PARA_CAJA: "la prenda está lista para continuar el
proceso", nunca "venta creada". Sin botones de vender/cobrar/comprobante:
eso es CU24 (Registrar venta presencial) y CU25 (Procesar pago presencial),
todavía fuera de alcance -- esta consulta es únicamente la puerta preparada
para cuando esos CU existan.

Flujo de estados que administra este paquete, por detalle (ver
Models/reserva.py para el enum completo):

    PENDIENTE -> PREPARADA -> EN_ATENCION -> ATENDIDA (sin compra)
                                           -> LISTA_PARA_CAJA (deriva a caja)
    PENDIENTE -> EN_ATENCION (el Cliente llega sin haber pasado por PREPARADA)
    PENDIENTE | PREPARADA -> VENCIDA (nunca llegó, venció su bloque horario)

Reutiliza (sin duplicar) lo que CU17/CU18/CU19 ya dejaron funcionando:
  - Reserva/ReservaDetalle y StockSucursal.stock_reservado (agregado por CU17);
  - el mismo patrón de lock SELECT ... FOR UPDATE que ya usan
    CU17_CrearReservaPrendas y CU19_CancelarReserva para evitar condiciones
    de carrera al cambiar estado y liberar stock en la misma transacción.

CU20 define su PROPIO contrato de salida (schemas.py) en vez de reutilizar
ReservaOut de CU17: el panel del Encargado necesita datos que la vista del
Cliente nunca expone (nombre/correo de quién reservó) y nunca depende de
`cliente_id` para autorizar nada.

Vencimiento reactivo (sección 6): `service.py` expone `expirar_vencidas`,
la única función que CU17_CrearReservaPrendas/service.py importa desde aquí
-- para que "Mis reservas" (CU18) nunca muestre como PENDIENTE/PREPARADA una
reserva cuyo bloque horario ya pasó. Es la única dependencia cruzada; nada
de CU17/CU18/CU19 se movió ni se duplicó.

NO implementa ventas, pagos, comprobantes, pantalla de cajero ni descuento de
stock físico -- LISTA_PARA_CAJA es únicamente un marcador persistente para un
proceso futuro fuera de este alcance.
"""
