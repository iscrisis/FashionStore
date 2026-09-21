import '../../core/network/api_client.dart';
import 'models/compra_digital.dart';

/// Consume CU22 -- Realizar compra digital (Cliente). Requiere un CLIENTE
/// autenticado (mismo contrato que ya usa Angular, ver
/// frontend/web/.../compra-digital/compra-digital.service.ts). Los items
/// SIEMPRE salen del carrito propio ya `seleccionado` (CU21) en el backend
/// -- este servicio nunca envía item_ids, precios ni el total: FastAPI los
/// recalcula siempre al confirmar.
class CompraDigitalService {
  CompraDigitalService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<ResumenCompraOut> obtenerResumen({required String token}) async {
    final data = await _apiClient.get('/compra-digital/resumen', token: token);
    return ResumenCompraOut.fromJson(data as Map<String, dynamic>);
  }

  Future<List<SucursalCompraOut>> listarSucursales({required int ciudadId, required String token}) async {
    final data = await _apiClient.get(
      '/compra-digital/sucursales',
      token: token,
      query: {'ciudad_id': ciudadId},
    );
    return (data as List)
        .map((item) => SucursalCompraOut.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<VentaOut> confirmar({required int sucursalId, required String token}) async {
    final data = await _apiClient.post(
      '/compra-digital',
      token: token,
      body: {'sucursal_id': sucursalId},
    );
    return VentaOut.fromJson(data as Map<String, dynamic>);
  }
}
