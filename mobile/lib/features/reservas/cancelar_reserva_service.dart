import '../../core/network/api_client.dart';
import 'models/reserva.dart';

/// Consume CU19 -- Cancelar reserva (Cliente): reutiliza
/// `PATCH /reservas/detalles/{detalle_id}/cancelar`, el mismo endpoint que ya
/// usa Angular (ver frontend/web/.../cancelar-reserva/cancelar-reserva.service.ts).
/// Cancela SOLO ese detalle (una prenda dentro de una reserva), sin body --
/// el backend resuelve el dueño SIEMPRE del token, nunca de un cliente_id que
/// Flutter pudiera enviar. Cancelar la reserva ENTERA existe en el backend
/// (`PATCH /reservas/{id}/cancelar`) pero, igual que en Angular, esta pantalla
/// no lo expone: el Cliente cancela prenda por prenda.
class CancelarReservaService {
  CancelarReservaService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<ReservaDetalleOut> cancelarDetalle({required int detalleId, required String token}) async {
    final data = await _apiClient.patch('/reservas/detalles/$detalleId/cancelar', token: token);
    return ReservaDetalleOut.fromJson(data as Map<String, dynamic>);
  }
}
