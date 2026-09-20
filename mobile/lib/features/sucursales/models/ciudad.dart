/// Refleja `CiudadPublicaOut` (CU07 -- backend/modules/P1_SucursalesYCatalogos/
/// CU07_ConsultarSucursales/schemas.py).
class Ciudad {
  const Ciudad({required this.id, required this.nombre});

  final int id;
  final String nombre;

  factory Ciudad.fromJson(Map<String, dynamic> json) {
    return Ciudad(id: json['id'] as int, nombre: json['nombre'] as String);
  }
}
