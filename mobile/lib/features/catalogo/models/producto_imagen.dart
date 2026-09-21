/// Refleja `ProductoImagenOut` (CU11).
class ProductoImagen {
  const ProductoImagen({required this.id, required this.url, required this.orden});

  final int id;
  final String url;
  final int orden;

  factory ProductoImagen.fromJson(Map<String, dynamic> json) {
    return ProductoImagen(
      id: json['id'] as int,
      url: json['url'] as String,
      orden: json['orden'] as int,
    );
  }
}
