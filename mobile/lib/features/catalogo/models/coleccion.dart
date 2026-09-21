import 'temporada.dart';

/// Refleja `ColeccionOut` (CU11): usado tanto por el catálogo público como,
/// cruzado por id, para resolver el nombre real de la colección destacada
/// (ver CU10 -- /colecciones/destacada solo entrega id + imagen).
class Coleccion {
  const Coleccion({
    required this.id,
    required this.nombre,
    required this.temporada,
    this.descripcion,
  });

  final int id;
  final String nombre;
  final String? descripcion;
  final Temporada temporada;

  factory Coleccion.fromJson(Map<String, dynamic> json) {
    return Coleccion(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      descripcion: json['descripcion'] as String?,
      temporada: Temporada.fromJson(json['temporada'] as Map<String, dynamic>),
    );
  }
}
