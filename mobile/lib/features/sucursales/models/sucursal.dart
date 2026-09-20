import 'ciudad.dart';

/// Refleja exactamente `SucursalPublicaOut` (CU07). Público y de solo
/// lectura: el backend ya excluye "departamento"/"is_active" (campos
/// administrativos de CU06) -- no hay horario en el contrato real, así que
/// Flutter no lo muestra.
class Sucursal {
  const Sucursal({
    required this.id,
    required this.nombre,
    required this.direccion,
    required this.telefono,
    required this.ciudad,
  });

  final int id;
  final String nombre;
  final String direccion;
  final String telefono;
  final Ciudad ciudad;

  factory Sucursal.fromJson(Map<String, dynamic> json) {
    return Sucursal(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      direccion: json['direccion'] as String,
      telefono: json['telefono'] as String,
      ciudad: Ciudad.fromJson(json['ciudad'] as Map<String, dynamic>),
    );
  }
}
