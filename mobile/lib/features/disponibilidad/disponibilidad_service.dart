import '../../core/network/api_client.dart';
import 'models/producto_disponibilidad.dart';

/// Consume CU12 -- Consultar disponibilidad por sucursal (público, sin
/// token). Mismo contrato REST que ya usa Angular
/// (frontend/web/src/app/features/public/catalogo/producto-detalle/
/// disponibilidad.service.ts): el backend siempre responde con todas las
/// variantes del producto por sucursal: no filtra por talla/color server
/// side (se envían igual, por si un futuro ajuste del backend los usa) --
/// el filtrado real por variante ocurre en Flutter sobre `variantes`.
class DisponibilidadService {
  DisponibilidadService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<ProductoDisponibilidad> consultar({
    required int productoId,
    int? tallaId,
    int? colorId,
    int? ciudadId,
  }) async {
    final query = <String, dynamic>{'producto_id': productoId};
    if (tallaId != null) query['talla_id'] = tallaId;
    if (colorId != null) query['color_id'] = colorId;
    if (ciudadId != null) query['ciudad_id'] = ciudadId;

    final data = await _apiClient.get('/disponibilidad', query: query);
    return ProductoDisponibilidad.fromJson(data as Map<String, dynamic>);
  }
}
