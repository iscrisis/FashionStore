/// Refleja exactamente `CategoriaOut` de
/// backend/modules/P1_SucursalesYCatalogos/CU11_ConsultarCatalogoPrendas/schemas.py.
class Categoria {
  const Categoria({required this.id, required this.nombre, this.imagenUrl});

  final int id;
  final String nombre;
  final String? imagenUrl;

  factory Categoria.fromJson(Map<String, dynamic> json) {
    return Categoria(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      imagenUrl: json['imagen_url'] as String?,
    );
  }
}
