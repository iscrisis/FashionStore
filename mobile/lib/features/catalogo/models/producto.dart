import 'categoria.dart';
import 'coleccion.dart';
import 'color_opcion.dart';
import 'producto_imagen.dart';
import 'talla.dart';
import 'temporada.dart';

/// Refleja exactamente `ProductoOut` (CU11 -- catálogo público). Los precios
/// de promoción (`precio_final`, `en_promocion`, `porcentaje_descuento`)
/// SIEMPRE vienen ya calculados por FastAPI (CU32); Flutter nunca los
/// recalcula, solo los muestra.
class Producto {
  const Producto({
    required this.id,
    required this.nombre,
    required this.precioVenta,
    required this.precioBase,
    required this.precioFinal,
    required this.enPromocion,
    required this.imagenes,
    required this.categoria,
    required this.temporada,
    required this.coleccion,
    required this.tallas,
    required this.colores,
    this.descripcion,
    this.porcentajeDescuento,
    this.imagenPrincipalUrl,
  });

  final int id;
  final String nombre;
  final String? descripcion;
  final double precioVenta;
  final double precioBase;
  final double precioFinal;
  final bool enPromocion;
  final double? porcentajeDescuento;
  final String? imagenPrincipalUrl;
  final List<ProductoImagen> imagenes;
  final Categoria categoria;
  final Temporada temporada;
  final Coleccion coleccion;
  final List<Talla> tallas;
  final List<ColorOpcion> colores;

  factory Producto.fromJson(Map<String, dynamic> json) {
    return Producto(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      descripcion: json['descripcion'] as String?,
      precioVenta: (json['precio_venta'] as num).toDouble(),
      precioBase: (json['precio_base'] as num).toDouble(),
      precioFinal: (json['precio_final'] as num).toDouble(),
      enPromocion: json['en_promocion'] as bool,
      porcentajeDescuento: (json['porcentaje_descuento'] as num?)?.toDouble(),
      imagenPrincipalUrl: json['imagen_principal_url'] as String?,
      imagenes: (json['imagenes'] as List)
          .map((e) => ProductoImagen.fromJson(e as Map<String, dynamic>))
          .toList(),
      categoria: Categoria.fromJson(json['categoria'] as Map<String, dynamic>),
      temporada: Temporada.fromJson(json['temporada'] as Map<String, dynamic>),
      coleccion: Coleccion.fromJson(json['coleccion'] as Map<String, dynamic>),
      tallas: (json['tallas'] as List)
          .map((e) => Talla.fromJson(e as Map<String, dynamic>))
          .toList(),
      colores: (json['colores'] as List)
          .map((e) => ColorOpcion.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
