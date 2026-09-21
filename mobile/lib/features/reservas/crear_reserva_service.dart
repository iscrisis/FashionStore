import '../../core/network/api_client.dart';
import 'models/reserva.dart';

/// Consume CU17 -- Crear reserva de prendas (`POST /reservas`). Requiere un
/// CLIENTE autenticado (mismo contrato que ya usa Angular, ver
/// frontend/web/.../reservas/crear-reserva/crear-reserva.service.ts).
/// cantidad siempre es 1: CU17 todavía no expone un carrito (fuera de
/// alcance, ver CU21), el Cliente reserva una prenda a la vez.
class CrearReservaService {
  CrearReservaService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<ReservaOut> crear({
    required int productoVarianteId,
    required int sucursalId,
    required String fechaReserva,
    required String horaInicio,
    required String token,
  }) async {
    final data = await _apiClient.post(
      '/reservas',
      token: token,
      body: {
        'producto_variante_id': productoVarianteId,
        'sucursal_id': sucursalId,
        'cantidad': 1,
        'fecha_reserva': fechaReserva,
        'hora_inicio': horaInicio,
      },
    );
    return ReservaOut.fromJson(data as Map<String, dynamic>);
  }
}
