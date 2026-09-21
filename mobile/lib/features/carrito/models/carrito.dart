/// Refleja 1:1 los contratos de CU21 -- Usar carrito de compras
/// (backend/modules/P5_ComprasVentasYPagos/CU21_UsarCarritoCompras/schemas.py),
/// los mismos que ya consume Angular (frontend/web/.../carrito/carrito.model.ts).
///
/// El carrito es SOLO intención de compra digital -- nunca una Reserva
/// (CU17). Cada [CarritoItemOut] es UNA unidad concreta de una variante: NO
/// existe un campo `cantidad` -- agregar la misma variante otra vez crea
/// OTRO item independiente, con su propio `itemId` y su propio
/// `seleccionado` (el checkbox del carrito, para marcar qué unidades se
/// consideran en una compra futura). `precioUnitario` es SIEMPRE el precio
/// EFECTIVO vigente al consultar, nunca un valor guardado.
library;

class TallaResumen {
  const TallaResumen({required this.id, required this.nombre});

  final int id;
  final String nombre;

  factory TallaResumen.fromJson(Map<String, dynamic> json) {
    return TallaResumen(id: json['id'] as int, nombre: json['nombre'] as String);
  }
}

class ColorResumen {
  const ColorResumen({required this.id, required this.nombre});

  final int id;
  final String nombre;

  factory ColorResumen.fromJson(Map<String, dynamic> json) {
    return ColorResumen(id: json['id'] as int, nombre: json['nombre'] as String);
  }
}

class VarianteResumen {
  const VarianteResumen({required this.id, required this.talla, required this.color});

  final int id;
  final TallaResumen talla;
  final ColorResumen color;

  factory VarianteResumen.fromJson(Map<String, dynamic> json) {
    return VarianteResumen(
      id: json['id'] as int,
      talla: TallaResumen.fromJson(json['talla'] as Map<String, dynamic>),
      color: ColorResumen.fromJson(json['color'] as Map<String, dynamic>),
    );
  }
}

class ProductoResumen {
  const ProductoResumen({required this.id, required this.nombre, this.imagenPrincipalUrl});

  final int id;
  final String nombre;
  final String? imagenPrincipalUrl;

  factory ProductoResumen.fromJson(Map<String, dynamic> json) {
    return ProductoResumen(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      imagenPrincipalUrl: json['imagen_principal_url'] as String?,
    );
  }
}

class CarritoItemOut {
  const CarritoItemOut({
    required this.itemId,
    required this.productoVarianteId,
    required this.producto,
    required this.variante,
    required this.precioUnitario,
    required this.precioBase,
    required this.enPromocion,
    required this.seleccionado,
    this.porcentajeDescuento,
  });

  final int itemId;
  final int productoVarianteId;
  final ProductoResumen producto;
  final VarianteResumen variante;
  final double precioUnitario;
  final double precioBase;
  final bool enPromocion;
  final double? porcentajeDescuento;
  final bool seleccionado;

  factory CarritoItemOut.fromJson(Map<String, dynamic> json) {
    return CarritoItemOut(
      itemId: json['item_id'] as int,
      productoVarianteId: json['producto_variante_id'] as int,
      producto: ProductoResumen.fromJson(json['producto'] as Map<String, dynamic>),
      variante: VarianteResumen.fromJson(json['variante'] as Map<String, dynamic>),
      precioUnitario: (json['precio_unitario'] as num).toDouble(),
      precioBase: (json['precio_base'] as num).toDouble(),
      enPromocion: json['en_promocion'] as bool,
      porcentajeDescuento: (json['porcentaje_descuento'] as num?)?.toDouble(),
      seleccionado: json['seleccionado'] as bool,
    );
  }
}

class CarritoOut {
  const CarritoOut({required this.items, required this.subtotalSeleccionado, required this.fechaActualizacion});

  final List<CarritoItemOut> items;
  final double subtotalSeleccionado;
  final String fechaActualizacion;

  factory CarritoOut.fromJson(Map<String, dynamic> json) {
    return CarritoOut(
      items: (json['items'] as List)
          .map((item) => CarritoItemOut.fromJson(item as Map<String, dynamic>))
          .toList(),
      subtotalSeleccionado: (json['subtotal_seleccionado'] as num).toDouble(),
      fechaActualizacion: json['fecha_actualizacion'] as String,
    );
  }
}
