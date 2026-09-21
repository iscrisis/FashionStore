/// Refleja 1:1 los contratos de CU23 -- Procesar pago electrónico
/// (backend/modules/P5_ComprasVentasYPagos/CU23_ProcesarPagoElectronico/schemas.py).
/// Stripe Checkout Hosted (modo TEST) es el ÚNICO proveedor real para este
/// CU -- ver app/integrations/stripe_client.py. Angular nunca envía monto,
/// tarjeta ni estado: solo `venta_id` (para pedir el Checkout) o
/// `session_id` (para pedir la verificación); Flutter hace exactamente lo
/// mismo.
library;

/// Únicamente la URL segura de Checkout -- ni Angular ni Flutter reciben
/// nada más de Stripe (ni el `session_id`, que solo vuelve a aparecer en la
/// propia URL de retorno que arma FastAPI).
class CheckoutSessionOut {
  const CheckoutSessionOut({required this.checkoutUrl});

  final String checkoutUrl;

  factory CheckoutSessionOut.fromJson(Map<String, dynamic> json) {
    return CheckoutSessionOut(checkoutUrl: json['checkout_url'] as String);
  }
}

class SucursalVentaOut {
  const SucursalVentaOut({
    required this.id,
    required this.nombre,
    required this.direccion,
    required this.ciudad,
  });

  final int id;
  final String nombre;
  final String direccion;
  final String ciudad;

  factory SucursalVentaOut.fromJson(Map<String, dynamic> json) {
    return SucursalVentaOut(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      direccion: json['direccion'] as String,
      ciudad: json['ciudad'] as String,
    );
  }
}

/// Solo se construye DESPUÉS de que FastAPI confirmó el pago contra Stripe
/// (ver CU23.../service.py:verificar_pago) -- `estado` siempre vale
/// "PAGADA" en esta salida real (nunca "PENDIENTE_PAGO" aquí, según el
/// propio contrato del backend); se guarda como `String` tal cual porque el
/// schema del backend la declara `str`, no un enum.
class VentaPagadaOut {
  const VentaPagadaOut({
    required this.id,
    required this.codigoVenta,
    required this.estado,
    required this.total,
    required this.sucursal,
  });

  final int id;
  final String codigoVenta;
  final String estado;
  final double total;
  final SucursalVentaOut sucursal;

  factory VentaPagadaOut.fromJson(Map<String, dynamic> json) {
    return VentaPagadaOut(
      id: json['id'] as int,
      codigoVenta: json['codigo_venta'] as String,
      estado: json['estado'] as String,
      total: (json['total'] as num).toDouble(),
      sucursal: SucursalVentaOut.fromJson(json['sucursal'] as Map<String, dynamic>),
    );
  }
}
