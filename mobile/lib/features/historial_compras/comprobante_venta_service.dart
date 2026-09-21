import '../../core/network/api_client.dart';
import 'models/comprobante_venta.dart';

/// Consume CU31 -- Emitir comprobante de venta (`GET /comprobantes/{venta_id}`),
/// reutilizado tal cual como detalle de compra para CU27 -- el propio backend
/// deja este endpoint preparado para ese fin (ver
/// CU31_EmitirComprobanteVenta/router.py). La autorización (esta Venta es del
/// Cliente autenticado) ya la valida el backend, nunca Flutter.
class ComprobanteVentaService {
  ComprobanteVentaService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<ComprobanteVentaOut> obtenerComprobante({required int ventaId, required String token}) async {
    final data = await _apiClient.get('/comprobantes/$ventaId', token: token);
    return ComprobanteVentaOut.fromJson(data as Map<String, dynamic>);
  }
}
