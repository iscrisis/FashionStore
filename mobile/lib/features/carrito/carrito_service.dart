import '../../core/network/api_client.dart';
import 'models/carrito.dart';

/// Consume CU21 -- Usar carrito de compras (Cliente). Requiere un CLIENTE
/// autenticado (mismo contrato que ya usa Angular, ver
/// frontend/web/.../carrito/carrito.service.ts). `cliente_id` se resuelve
/// SIEMPRE del token en el backend -- Flutter nunca lo envía. Cada mutación
/// devuelve el [CarritoOut] COMPLETO ya actualizado (nunca un item aislado),
/// mismo criterio que CU17/CU18.
class CarritoService {
  CarritoService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<CarritoOut> consultar({required String token}) async {
    final data = await _apiClient.get('/carrito', token: token);
    return CarritoOut.fromJson(data as Map<String, dynamic>);
  }

  /// Agrega SIEMPRE una sola unidad -- sin `cantidad`: para dos unidades de
  /// la misma variante, se llama este método dos veces (ver
  /// AgregarItemRequest en el backend).
  Future<CarritoOut> agregarItem({required int productoVarianteId, required String token}) async {
    final data = await _apiClient.post(
      '/carrito/items',
      token: token,
      body: {'producto_variante_id': productoVarianteId},
    );
    return CarritoOut.fromJson(data as Map<String, dynamic>);
  }

  /// Marca/desmarca una unidad puntual para una compra futura -- no crea
  /// Venta ni Pago (CU22, fuera de este alcance).
  Future<CarritoOut> actualizarSeleccion({
    required int itemId,
    required bool seleccionado,
    required String token,
  }) async {
    final data = await _apiClient.patch(
      '/carrito/items/$itemId',
      token: token,
      body: {'seleccionado': seleccionado},
    );
    return CarritoOut.fromJson(data as Map<String, dynamic>);
  }

  Future<CarritoOut> eliminarItem({required int itemId, required String token}) async {
    final data = await _apiClient.delete('/carrito/items/$itemId', token: token);
    return CarritoOut.fromJson(data as Map<String, dynamic>);
  }
}
