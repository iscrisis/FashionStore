/// Refleja 1:1 los contratos de CU31 -- Emitir comprobante de venta
/// (backend/modules/P5_ComprasVentasYPagos/CU31_EmitirComprobanteVenta/
/// schemas.py). El propio backend deja preparado este mismo endpoint
/// (`GET /comprobantes/{venta_id}`) para que CU27 lo reutilice tal cual como
/// detalle de una compra -- por eso Flutter también lo consume aquí, sin
/// pedir un endpoint nuevo.
library;

class TallaComprobanteResumen {
  const TallaComprobanteResumen({required this.id, required this.nombre});

  final int id;
  final String nombre;

  factory TallaComprobanteResumen.fromJson(Map<String, dynamic> json) {
    return TallaComprobanteResumen(id: json['id'] as int, nombre: json['nombre'] as String);
  }
}

class ColorComprobanteResumen {
  const ColorComprobanteResumen({required this.id, required this.nombre});

  final int id;
  final String nombre;

  factory ColorComprobanteResumen.fromJson(Map<String, dynamic> json) {
    return ColorComprobanteResumen(id: json['id'] as int, nombre: json['nombre'] as String);
  }
}

class VarianteComprobanteResumen {
  const VarianteComprobanteResumen({required this.id, required this.talla, required this.color});

  final int id;
  final TallaComprobanteResumen talla;
  final ColorComprobanteResumen color;

  factory VarianteComprobanteResumen.fromJson(Map<String, dynamic> json) {
    return VarianteComprobanteResumen(
      id: json['id'] as int,
      talla: TallaComprobanteResumen.fromJson(json['talla'] as Map<String, dynamic>),
      color: ColorComprobanteResumen.fromJson(json['color'] as Map<String, dynamic>),
    );
  }
}

class ProductoComprobanteResumen {
  const ProductoComprobanteResumen({required this.id, required this.nombre, this.imagenPrincipalUrl});

  final int id;
  final String nombre;
  final String? imagenPrincipalUrl;

  factory ProductoComprobanteResumen.fromJson(Map<String, dynamic> json) {
    return ProductoComprobanteResumen(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      imagenPrincipalUrl: json['imagen_principal_url'] as String?,
    );
  }
}

class SucursalComprobanteOut {
  const SucursalComprobanteOut({
    required this.id,
    required this.nombre,
    required this.direccion,
    required this.ciudad,
  });

  final int id;
  final String nombre;
  final String direccion;
  final String ciudad;

  factory SucursalComprobanteOut.fromJson(Map<String, dynamic> json) {
    return SucursalComprobanteOut(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      direccion: json['direccion'] as String,
      ciudad: json['ciudad'] as String,
    );
  }
}

class DetalleComprobanteOut {
  const DetalleComprobanteOut({
    required this.producto,
    required this.variante,
    required this.cantidad,
    required this.precioUnitario,
    required this.subtotal,
  });

  final ProductoComprobanteResumen producto;
  final VarianteComprobanteResumen variante;
  final int cantidad;
  final double precioUnitario;
  final double subtotal;

  factory DetalleComprobanteOut.fromJson(Map<String, dynamic> json) {
    return DetalleComprobanteOut(
      producto: ProductoComprobanteResumen.fromJson(json['producto'] as Map<String, dynamic>),
      variante: VarianteComprobanteResumen.fromJson(json['variante'] as Map<String, dynamic>),
      cantidad: json['cantidad'] as int,
      precioUnitario: (json['precio_unitario'] as num).toDouble(),
      subtotal: (json['subtotal'] as num).toDouble(),
    );
  }
}

class ComprobanteVentaOut {
  const ComprobanteVentaOut({
    required this.ventaId,
    required this.codigoVenta,
    required this.fechaCreacion,
    required this.tipo,
    required this.sucursal,
    required this.detalles,
    required this.total,
    required this.metodoPago,
    required this.estado,
    required this.estadoPago,
  });

  final int ventaId;
  final String codigoVenta;
  final String fechaCreacion; // ISO 8601
  final String tipo;
  final SucursalComprobanteOut sucursal;
  final List<DetalleComprobanteOut> detalles;
  final double total;
  final String metodoPago;
  final String estado;
  final String estadoPago;

  factory ComprobanteVentaOut.fromJson(Map<String, dynamic> json) {
    return ComprobanteVentaOut(
      ventaId: json['venta_id'] as int,
      codigoVenta: json['codigo_venta'] as String,
      fechaCreacion: json['fecha_creacion'] as String,
      tipo: json['tipo'] as String,
      sucursal: SucursalComprobanteOut.fromJson(json['sucursal'] as Map<String, dynamic>),
      detalles: (json['detalles'] as List)
          .map((item) => DetalleComprobanteOut.fromJson(item as Map<String, dynamic>))
          .toList(),
      total: (json['total'] as num).toDouble(),
      metodoPago: json['metodo_pago'] as String,
      estado: json['estado'] as String,
      estadoPago: json['estado_pago'] as String,
    );
  }
}
