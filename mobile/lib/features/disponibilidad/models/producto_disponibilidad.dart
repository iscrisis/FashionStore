import 'disponibilidad_sucursal.dart';

/// Refleja `ProductoDisponibilidadOut` (CU12) -- respuesta completa de
/// `GET /disponibilidad?producto_id=&ciudad_id=`.
class ProductoDisponibilidad {
  const ProductoDisponibilidad({required this.productoId, required this.disponibilidad});

  final int productoId;
  final List<DisponibilidadSucursal> disponibilidad;

  factory ProductoDisponibilidad.fromJson(Map<String, dynamic> json) {
    return ProductoDisponibilidad(
      productoId: json['producto_id'] as int,
      disponibilidad: (json['disponibilidad'] as List)
          .map((item) => DisponibilidadSucursal.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
