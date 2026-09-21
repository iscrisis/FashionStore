/// Refleja 1:1 los contratos de CU27 -- Consultar historial de compras
/// (backend/modules/P5_ComprasVentasYPagos/CU27_ConsultarHistorialCompras/
/// schemas.py). `VentaHistorialOut` es una fila del historial -- SIEMPRE de
/// una Venta PAGADA (el backend nunca devuelve otro estado en este listado).
library;

class CiudadHistorialResumen {
  const CiudadHistorialResumen({required this.nombre});

  final String nombre;
}

class SucursalHistorialOut {
  const SucursalHistorialOut({required this.id, required this.nombre, required this.ciudad});

  final int id;
  final String nombre;
  final String ciudad;

  factory SucursalHistorialOut.fromJson(Map<String, dynamic> json) {
    return SucursalHistorialOut(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      ciudad: json['ciudad'] as String,
    );
  }
}

class VentaHistorialOut {
  const VentaHistorialOut({
    required this.ventaId,
    required this.codigoVenta,
    required this.fecha,
    required this.sucursal,
    required this.clienteNombre,
    required this.tipo,
    required this.metodoPago,
    required this.total,
    required this.tienePostventa,
    required this.leyendaPostventa,
  });

  final int ventaId;
  final String codigoVenta;
  final String fecha; // ISO 8601
  final SucursalHistorialOut sucursal;
  final String? clienteNombre;
  final String tipo;
  final String metodoPago;
  final double total;
  final bool tienePostventa;
  final String? leyendaPostventa;

  factory VentaHistorialOut.fromJson(Map<String, dynamic> json) {
    return VentaHistorialOut(
      ventaId: json['venta_id'] as int,
      codigoVenta: json['codigo_venta'] as String,
      fecha: json['fecha'] as String,
      sucursal: SucursalHistorialOut.fromJson(json['sucursal'] as Map<String, dynamic>),
      clienteNombre: json['cliente_nombre'] as String?,
      tipo: json['tipo'] as String,
      metodoPago: json['metodo_pago'] as String,
      total: (json['total'] as num).toDouble(),
      tienePostventa: json['tiene_postventa'] as bool,
      leyendaPostventa: json['leyenda_postventa'] as String?,
    );
  }
}
