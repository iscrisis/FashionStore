"""CU19 -- Cancelar reserva (Cliente).

El Cliente autenticado cancela SOLO reservas/detalles propios, y SOLO los que
siguen PENDIENTE o PREPARADA (ver service.py -- desde EN_ATENCION en
adelante el Encargado ya empezó a atenderla, CU20). Nada se borra de
PostgreSQL -- cambia de estado a CANCELADA, igual que documenta
Models/reserva.py. No se puede modificar fecha, hora, sucursal, talla, color
ni producto: CU19 es exclusivamente cancelar.

Dos operaciones, ambas expuestas por router.py:
  - cancelar UN detalle (una prenda dentro de una reserva), sin tocar el
    resto -- ej. el Cliente ya no quiere la camisa pero sigue queriendo la
    chaqueta y el pantalón.
  - cancelar la reserva ENTERA -- todos los detalles todavía cancelables
    pasan a CANCELADA; uno que ya avanzó más (EN_ATENCION en adelante) queda
    intacto.

Reutiliza (sin duplicar) lo que CU17/CU18 ya dejaron funcionando:
  - Reserva/ReservaDetalle y EstadoReserva (P4_ReservasYAtencion/Models),
    incluido `Reserva.recalcular_estado_general()` tras cada cancelación;
  - StockSucursal.stock_reservado, agregado por CU17 -- cancelar hace la
    operación inversa a crear: libera esa misma columna, nunca toca
    `cantidad` (el stock físico realmente no se movió);
  - los contratos ReservaOut/ReservaDetalleOut (CU17_CrearReservaPrendas/schemas.py)
    para la respuesta -- Angular y, más adelante, Flutter ya saben leer esa
    forma exacta desde CU18.

La lógica de negocio propia de CU19 (verificar dueño, verificar estado
cancelable, liberar stock_reservado con SELECT ... FOR UPDATE, cambiar el
estado) es nueva y vive completa en este paquete -- no se agrega nada a CU17
ni a CU18.
"""
