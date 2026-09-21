import '../../core/network/api_client.dart';
import 'models/pago_electronico.dart';

/// Consume CU23 -- Procesar pago electrónico (Cliente). Requiere un CLIENTE
/// autenticado. `cliente_id` se resuelve SIEMPRE del token en el backend --
/// Flutter nunca lo envía, tampoco el monto (siempre `Venta.total`,
/// calculado por FastAPI en CU22).
class PagoElectronicoService {
  PagoElectronicoService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  /// `platform: "mobile"` es lo único que distingue esta llamada de la que
  /// hace Angular (ver backend .../CU23_ProcesarPagoElectronico/router.py):
  /// con eso, Stripe redirige de vuelta a
  /// `fashionstore://pago/resultado` (ver deep_link_service.dart) en vez de
  /// a la web -- Angular nunca envía este campo, así que su comportamiento
  /// no cambia.
  Future<CheckoutSessionOut> crearCheckout({required int ventaId, required String token}) async {
    final data = await _apiClient.post(
      '/pagos/checkout',
      token: token,
      body: {'venta_id': ventaId, 'platform': 'mobile'},
    );
    return CheckoutSessionOut.fromJson(data as Map<String, dynamic>);
  }

  Future<VentaPagadaOut> verificarPago({required String sessionId, required String token}) async {
    final data = await _apiClient.post(
      '/pagos/verificar',
      token: token,
      body: {'session_id': sessionId},
    );
    return VentaPagadaOut.fromJson(data as Map<String, dynamic>);
  }
}
