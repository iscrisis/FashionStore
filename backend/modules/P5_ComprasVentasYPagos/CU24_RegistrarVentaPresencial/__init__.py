"""CU24 -- Registrar venta presencial (Cajero).

Arma y registra una Venta PRESENCIAL (PENDIENTE_PAGO), reutilizando el
mismo modelo Venta/VentaDetalle que ya crea CU22 -- no es un sistema de
ventas paralelo, solo un tipo/origen distinto sobre la misma tabla. Dos
formas de armarla:
  - DIRECTA: el Cliente entra a tienda sin reserva, el Cajero busca
    productos y arma las líneas a mano.
  - RESERVA: el Cajero carga una Reserva que CU20 ya dejó LISTA_PARA_CAJA
    en su sucursal, con las prendas que el Cliente decidió llevarse.

CU24 NUNCA procesa el pago (CU25, fuera de este alcance) ni toca stock
(`stock_actual`/`stock_reservado`): solo valida disponibilidad y registra la
intención de venta. Tampoco cambia el estado de la Reserva ni de sus
detalles -- sigue LISTA_PARA_CAJA hasta que CU25 confirme el pago.
"""
