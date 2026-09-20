import '../../core/network/api_client.dart';
import 'models/ciudad.dart';
import 'models/sucursal.dart';

/// Consume CU07 -- Consultar sucursales (público, sin token). Mismos
/// contratos REST que ya usa Angular
/// (frontend/web/src/app/features/public/sucursales/sucursal.service.ts).
class SucursalesService {
  SucursalesService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<List<Ciudad>> listarCiudades() async {
    final data = await _apiClient.get('/sucursales-publicas/ciudades');
    return (data as List)
        .map((item) => Ciudad.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<Sucursal>> listarSucursales({int? ciudadId}) async {
    final query = ciudadId != null ? {'ciudad_id': ciudadId} : null;
    final data = await _apiClient.get('/sucursales-publicas/sucursales', query: query);
    return (data as List)
        .map((item) => Sucursal.fromJson(item as Map<String, dynamic>))
        .toList();
  }
}
