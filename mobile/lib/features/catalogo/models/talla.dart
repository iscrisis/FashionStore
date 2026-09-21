/// Refleja `TallaOut` (CU11).
class Talla {
  const Talla({required this.id, required this.nombre});

  final int id;
  final String nombre;

  factory Talla.fromJson(Map<String, dynamic> json) {
    return Talla(id: json['id'] as int, nombre: json['nombre'] as String);
  }
}
