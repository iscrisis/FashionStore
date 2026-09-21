import '../../core/network/api_client.dart';
import 'models/categoria.dart';
import 'models/coleccion.dart';
import 'models/coleccion_destacada.dart';
import 'models/color_opcion.dart';
import 'models/producto.dart';
import 'models/talla.dart';

/// Consume el catálogo público (CU11) y la colección destacada (CU10) --
/// exactamente los mismos contratos REST que ya usa Angular
/// (frontend/web/src/app/features/public/catalogo/catalogo.service.ts).
/// Sin token: son endpoints públicos, aptos para Invitado y Cliente.
class CatalogoService {
  CatalogoService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<List<Categoria>> listarCategorias() async {
    final data = await _apiClient.get('/catalogo/categorias');
    return (data as List)
        .map((item) => Categoria.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<Producto>> listarProductos({
    int? categoriaId,
    int? coleccionId,
    int? tallaId,
    int? colorId,
    String? search,
  }) async {
    final query = <String, dynamic>{};
    if (categoriaId != null) query['categoria_id'] = categoriaId;
    if (coleccionId != null) query['coleccion_id'] = coleccionId;
    if (tallaId != null) query['talla_id'] = tallaId;
    if (colorId != null) query['color_id'] = colorId;
    if (search != null && search.trim().isNotEmpty) {
      query['search'] = search.trim();
    }
    final data = await _apiClient.get(
      '/catalogo/productos',
      query: query.isEmpty ? null : query,
    );
    return (data as List)
        .map((item) => Producto.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<Talla>> listarTallas() async {
    final data = await _apiClient.get('/catalogo/tallas');
    return (data as List)
        .map((item) => Talla.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<ColorOpcion>> listarColores() async {
    final data = await _apiClient.get('/catalogo/colores');
    return (data as List)
        .map((item) => ColorOpcion.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<Coleccion>> listarColecciones({int? temporadaId}) async {
    final query = temporadaId != null ? {'temporada_id': temporadaId} : null;
    final data = await _apiClient.get('/catalogo/colecciones', query: query);
    return (data as List)
        .map((item) => Coleccion.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  /// CU10 -- /colecciones/destacada (fuera del prefijo /catalogo, es un dato
  /// propio de la gestión de temporadas/colecciones). Devuelve `null` si el
  /// Administrador no marcó ninguna colección como destacada.
  Future<ColeccionDestacada?> obtenerColeccionDestacada() async {
    final data = await _apiClient.get('/colecciones/destacada');
    if (data == null) return null;
    return ColeccionDestacada.fromJson(data as Map<String, dynamic>);
  }
}
