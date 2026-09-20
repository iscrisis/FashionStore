import 'variante_disponible.dart';

/// Refleja `DisponibilidadSucursalOut` (CU12). Por cada sucursal, trae
/// TODAS las variantes (talla+color) activas del producto -- el filtrado a
/// la variante que el Cliente eligió (talla+color) ocurre en Flutter sobre
/// esta misma lista, igual que ya lo hace Angular (no hay endpoint que
/// filtre por variante en el backend).
class DisponibilidadSucursal {
  const DisponibilidadSucursal({
    required this.sucursalId,
    required this.sucursal,
    required this.ciudadId,
    required this.ciudad,
    required this.variantes,
  });

  final int sucursalId;
  final String sucursal;
  final int ciudadId;
  final String ciudad;
  final List<VarianteDisponible> variantes;

  factory DisponibilidadSucursal.fromJson(Map<String, dynamic> json) {
    return DisponibilidadSucursal(
      sucursalId: json['sucursal_id'] as int,
      sucursal: json['sucursal'] as String,
      ciudadId: json['ciudad_id'] as int,
      ciudad: json['ciudad'] as String,
      variantes: (json['variantes'] as List)
          .map((item) => VarianteDisponible.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }

  /// Cantidad real disponible para la variante talla+color indicada en
  /// esta sucursal, o `null` si esa combinación no aparece aquí. Es una
  /// simple búsqueda en una lista ya resuelta por FastAPI -- no es un
  /// cálculo de stock.
  VarianteDisponible? varianteDe({required int tallaId, required int colorId}) {
    for (final variante in variantes) {
      if (variante.tallaId == tallaId && variante.colorId == colorId) {
        return variante;
      }
    }
    return null;
  }
}
