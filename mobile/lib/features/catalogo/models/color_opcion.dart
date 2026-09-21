/// Refleja `ColorOut` (CU11). Se llama `ColorOpcion` (no `Color`) para no
/// chocar con `dart:ui`'s `Color`.
class ColorOpcion {
  const ColorOpcion({required this.id, required this.nombre});

  final int id;
  final String nombre;

  factory ColorOpcion.fromJson(Map<String, dynamic> json) {
    return ColorOpcion(id: json['id'] as int, nombre: json['nombre'] as String);
  }
}
