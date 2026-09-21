import '../../core/network/api_client.dart';
import 'models/historial_compra.dart';

/// Consume CU27 -- Consultar historial de compras (Cliente): reutiliza
/// `GET /historial-compras/mias`, el mismo endpoint pensado para Angular
/// (ver backend CU27_ConsultarHistorialCompras/schemas.py -- "Flutter
/// reutilizará estos mismos endpoints tal cual"). `cliente_id` se resuelve
/// SIEMPRE del token en el backend -- Flutter nunca lo envía ni lo decide.
class HistorialComprasService {
  HistorialComprasService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  /// `desde`/`hasta` en formato "YYYY-MM-DD" (ver compra_formato.dart) --
  /// mismos 3 filtros opcionales que `FiltroHistorial` en Angular
  /// (historial-compras.model.ts), combinables libremente. Nunca se envía
  /// `cliente_id`: el backend lo resuelve siempre del token.
  Future<List<VentaHistorialOut>> listarMias({
    required String token,
    String? desde,
    String? hasta,
    String? codigoVenta,
  }) async {
    final query = <String, dynamic>{
      'desde': ?desde,
      'hasta': ?hasta,
      if (codigoVenta != null && codigoVenta.isNotEmpty) 'codigo_venta': codigoVenta,
    };
    final data = await _apiClient.get(
      '/historial-compras/mias',
      query: query.isEmpty ? null : query,
      token: token,
    );
    return (data as List).map((item) => VentaHistorialOut.fromJson(item as Map<String, dynamic>)).toList();
  }
}
