/// Refleja `VarianteDisponibleOut` (CU12 -- backend/modules/
/// P1_SucursalesYCatalogos/CU12_ConsultarDisponibilidadPorSucursal/schemas.py).
/// `cantidad` ya es lo REALMENTE disponible (stock físico menos reservas
/// pendientes) -- Flutter nunca la recalcula, solo la lee.
class VarianteDisponible {
  const VarianteDisponible({
    required this.productoVarianteId,
    required this.tallaId,
    required this.talla,
    required this.colorId,
    required this.color,
    required this.cantidad,
  });

  final int productoVarianteId;
  final int tallaId;
  final String talla;
  final int colorId;
  final String color;
  final int cantidad;

  factory VarianteDisponible.fromJson(Map<String, dynamic> json) {
    return VarianteDisponible(
      productoVarianteId: json['producto_variante_id'] as int,
      tallaId: json['talla_id'] as int,
      talla: json['talla'] as String,
      colorId: json['color_id'] as int,
      color: json['color'] as String,
      cantidad: json['cantidad'] as int,
    );
  }
}
