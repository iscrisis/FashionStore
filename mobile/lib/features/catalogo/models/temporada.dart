/// Refleja `TemporadaOut` (CU11) -- solo id + nombre.
class Temporada {
  const Temporada({required this.id, required this.nombre});

  final int id;
  final String nombre;

  factory Temporada.fromJson(Map<String, dynamic> json) {
    return Temporada(id: json['id'] as int, nombre: json['nombre'] as String);
  }
}
