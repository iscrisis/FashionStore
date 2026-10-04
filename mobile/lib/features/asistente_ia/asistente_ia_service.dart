import '../../core/network/api_client.dart';
import 'models/mensaje_asistente.dart';

/// Consume CU29 -- único punto por el que Flutter habla con el asistente;
/// nunca llama a Gemini directamente (ver docstring del backend, mismo
/// criterio que asistente-ia.service.ts en Angular). Apto para Invitado y
/// Cliente: el token se adjunta solo si hay sesión guardada (ver
/// widgets/asistente_ia_overlay.dart), pero el endpoint funciona igual sin
/// él.
///
/// Timeout propio de 45s (el `ApiClient` por defecto usa 10s, pensado para
/// el resto de endpoints, que son consultas directas a PostgreSQL) -- CU29
/// hace HASTA DOS llamadas a Gemini (interpretar + redactar) más la consulta
/// al catálogo, y en producción se midió una respuesta real de más de 30s.
/// Angular no tiene este problema porque su HttpClient no impone ningún
/// timeout: con los 10s por defecto, Flutter abortaba la espera antes de
/// que llegara la respuesta real (con `productos`) y mostraba el mensaje de
/// error genérico en su lugar, aunque el backend sí había respondido bien.
class AsistenteIaService {
  AsistenteIaService({ApiClient? apiClient})
      : _apiClient = apiClient ?? ApiClient(timeout: const Duration(seconds: 45));

  final ApiClient _apiClient;

  Future<MensajeAsistenteResponse> enviarMensaje({
    required String mensaje,
    required List<TurnoChat> historial,
    String? token,
  }) async {
    final data = await _apiClient.post(
      '/asistente-ia/mensaje',
      token: token,
      body: {
        'mensaje': mensaje,
        'historial': historial.map((turno) => turno.toJson()).toList(),
      },
    );
    return MensajeAsistenteResponse.fromJson(data as Map<String, dynamic>);
  }
}
