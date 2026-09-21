import '../../core/network/api_client.dart';
import 'models/reserva.dart';

/// Consume CU18 -- Consultar reserva (Cliente): reutiliza `GET /reservas/mias`,
/// el MISMO endpoint que ya expone CU17 (ver backend
/// modules/P4_ReservasYAtencion/CU18_ConsultarReserva/__init__.py -- "No hay
/// router/service/repository propios en este paquete", es el mismo contrato
/// que ya usa Angular en mis-reservas.service.ts). `cliente_id` se resuelve
/// SIEMPRE del token en el backend -- Flutter nunca lo envía ni lo decide.
class ConsultarReservasService {
  ConsultarReservasService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<List<ReservaOut>> listarMias({required String token}) async {
    final data = await _apiClient.get('/reservas/mias', token: token);
    return (data as List).map((item) => ReservaOut.fromJson(item as Map<String, dynamic>)).toList();
  }
}
