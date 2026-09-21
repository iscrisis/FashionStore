/// Refleja 1:1 los contratos de CU22 -- Realizar compra digital
/// (backend/modules/P5_ComprasVentasYPagos/CU22_RealizarCompraDigital/schemas.py),
/// los mismos que ya consume Angular (frontend/web/.../compra-digital.model.ts).
///
/// Los items de la compra son EXACTAMENTE los que el Cliente ya marcó
/// `seleccionado` en su carrito (CU21) -- nunca una lista nueva ni una
/// cantidad inventada aquí: cada línea sigue siendo UNA unidad concreta de
/// una variante (no existe `cantidad` en `LineaCompraOut`, igual que
/// CarritoItemOut). `precio_unitario` es SIEMPRE el precio EFECTIVO vigente
/// (CU32) hasta el momento de confirmar -- ahí recién queda histórico en
/// `VentaDetalleOut`.
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

/// Una prenda ya seleccionada en el carrito (CU21) -- pantalla "Finalizar
/// compra" antes de elegir sucursal.
class LineaCompraOut {
  const LineaCompraOut({
    required this.itemId,
    required this.productoVarianteId,
    required this.producto,
    required this.variante,
    required this.precioUnitario,
    required this.precioBase,
    required this.enPromocion,
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

  factory LineaCompraOut.fromJson(Map<String, dynamic> json) {
    return LineaCompraOut(
      itemId: json['item_id'] as int,
      productoVarianteId: json['producto_variante_id'] as int,
      producto: ProductoResumen.fromJson(json['producto'] as Map<String, dynamic>),
      variante: VarianteResumen.fromJson(json['variante'] as Map<String, dynamic>),
      precioUnitario: (json['precio_unitario'] as num).toDouble(),
      precioBase: (json['precio_base'] as num).toDouble(),
      enPromocion: json['en_promocion'] as bool,
      porcentajeDescuento: (json['porcentaje_descuento'] as num?)?.toDouble(),
    );
  }
}

class ResumenCompraOut {
  const ResumenCompraOut({required this.items, required this.total});

  final List<LineaCompraOut> items;
  final double total;

  factory ResumenCompraOut.fromJson(Map<String, dynamic> json) {
    return ResumenCompraOut(
      items: (json['items'] as List)
          .map((item) => LineaCompraOut.fromJson(item as Map<String, dynamic>))
          .toList(),
      total: (json['total'] as num).toDouble(),
    );
  }
}

/// Una sucursal activa de la ciudad elegida, con si puede o no cubrir TODA
/// la compra (todas las variantes seleccionadas a la vez) -- `disponible_para_compra`
/// lo calcula SIEMPRE el backend (ver CU22 service.py), nunca Flutter.
class SucursalCompraOut {
  const SucursalCompraOut({
    required this.id,
    required this.nombre,
    required this.direccion,
    required this.disponibleParaCompra,
  });

  final int id;
  final String nombre;
  final String direccion;
  final bool disponibleParaCompra;

  factory SucursalCompraOut.fromJson(Map<String, dynamic> json) {
    return SucursalCompraOut(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      direccion: json['direccion'] as String,
      disponibleParaCompra: json['disponible_para_compra'] as bool,
    );
  }
}

class SucursalVentaOut {
  const SucursalVentaOut({
    required this.id,
    required this.nombre,
    required this.direccion,
    required this.ciudad,
  });

  final int id;
  final String nombre;
  final String direccion;
  final String ciudad;

  factory SucursalVentaOut.fromJson(Map<String, dynamic> json) {
    return SucursalVentaOut(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      direccion: json['direccion'] as String,
      ciudad: json['ciudad'] as String,
    );
  }
}

class VentaDetalleOut {
  const VentaDetalleOut({
    required this.producto,
    required this.variante,
    required this.cantidad,
    required this.precioUnitario,
    required this.subtotal,
  });

  final ProductoResumen producto;
  final VarianteResumen variante;
  final int cantidad;
  final double precioUnitario;
  final double subtotal;

  factory VentaDetalleOut.fromJson(Map<String, dynamic> json) {
    return VentaDetalleOut(
      producto: ProductoResumen.fromJson(json['producto'] as Map<String, dynamic>),
      variante: VarianteResumen.fromJson(json['variante'] as Map<String, dynamic>),
      cantidad: json['cantidad'] as int,
      precioUnitario: (json['precio_unitario'] as num).toDouble(),
      subtotal: (json['subtotal'] as num).toDouble(),
    );
  }
}

/// Mismos 2 valores reales del backend (Models/venta.py: `EstadoVenta`) --
/// nunca se inventan estados nuevos. CU22 SIEMPRE crea la Venta en
/// `pendientePago`; `pagada` solo lo produce CU23 (pago electrónico, fuera
/// de este alcance) verificando directamente contra la pasarela de pago.
enum EstadoVenta {
  pendientePago,
  pagada;

  static EstadoVenta fromJson(String valor) {
    switch (valor) {
      case 'PENDIENTE_PAGO':
        return EstadoVenta.pendientePago;
      case 'PAGADA':
        return EstadoVenta.pagada;
      default:
        throw ArgumentError('Estado de venta desconocido: $valor');
    }
  }

  String get etiqueta {
    switch (this) {
      case EstadoVenta.pendientePago:
        return 'Pendiente de pago';
      case EstadoVenta.pagada:
        return 'Pagada';
    }
  }
}

/// La compra digital ya confirmada -- CU22 SIEMPRE la crea en
/// `PENDIENTE_PAGO` (ver Models/venta.py); cobrarla es CU23, fuera de este
/// alcance. `codigoVenta` (ej. "VT-00001") es el identificador visible para
/// el Cliente, nunca `id`.
class VentaOut {
  const VentaOut({
    required this.id,
    required this.codigoVenta,
    required this.sucursal,
    required this.tipo,
    required this.estado,
    required this.total,
    required this.fechaCreacion,
    required this.detalles,
  });

  final int id;
  final String codigoVenta;
  final SucursalVentaOut sucursal;
  final String tipo;
  final EstadoVenta estado;
  final double total;
  final String fechaCreacion;
  final List<VentaDetalleOut> detalles;

  factory VentaOut.fromJson(Map<String, dynamic> json) {
    return VentaOut(
      id: json['id'] as int,
      codigoVenta: json['codigo_venta'] as String,
      sucursal: SucursalVentaOut.fromJson(json['sucursal'] as Map<String, dynamic>),
      tipo: json['tipo'] as String,
      estado: EstadoVenta.fromJson(json['estado'] as String),
      total: (json['total'] as num).toDouble(),
      fechaCreacion: json['fecha_creacion'] as String,
      detalles: (json['detalles'] as List)
          .map((item) => VentaDetalleOut.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
