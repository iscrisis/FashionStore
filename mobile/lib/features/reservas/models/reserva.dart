/// Refleja 1:1 los contratos de CU17 -- Crear reserva de prendas
/// (backend/modules/P4_ReservasYAtencion/CU17_CrearReservaPrendas/schemas.py),
/// los mismos que ya consume Angular (frontend/web/.../crear-reserva.model.ts).
/// `ReservaOut` es la CABECERA de una reserva (una visita a una sucursal, en
/// un bloque horario) con sus prendas anidadas en `detalles`.
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

class CiudadResumen {
  const CiudadResumen({required this.id, required this.nombre});

  final int id;
  final String nombre;

  factory CiudadResumen.fromJson(Map<String, dynamic> json) {
    return CiudadResumen(id: json['id'] as int, nombre: json['nombre'] as String);
  }
}

class SucursalResumen {
  const SucursalResumen({required this.id, required this.nombre, required this.ciudad});

  final int id;
  final String nombre;
  final CiudadResumen ciudad;

  factory SucursalResumen.fromJson(Map<String, dynamic> json) {
    return SucursalResumen(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      ciudad: CiudadResumen.fromJson(json['ciudad'] as Map<String, dynamic>),
    );
  }
}

/// Mismos 7 valores reales del backend (Models/reserva.py: `EstadoReserva`)
/// -- nunca se inventan estados nuevos para Flutter. `etiqueta` es la ÚNICA
/// traducción visual (mismo texto que ya usa Angular, ver
/// frontend/web/.../reservas/estado-reserva.ts), puramente de presentación.
enum EstadoReserva {
  pendiente,
  preparada,
  enAtencion,
  listaParaCaja,
  cancelada,
  atendida,
  vencida;

  static EstadoReserva fromJson(String valor) {
    switch (valor) {
      case 'PENDIENTE':
        return EstadoReserva.pendiente;
      case 'PREPARADA':
        return EstadoReserva.preparada;
      case 'EN_ATENCION':
        return EstadoReserva.enAtencion;
      case 'LISTA_PARA_CAJA':
        return EstadoReserva.listaParaCaja;
      case 'CANCELADA':
        return EstadoReserva.cancelada;
      case 'ATENDIDA':
        return EstadoReserva.atendida;
      case 'VENCIDA':
        return EstadoReserva.vencida;
      default:
        throw ArgumentError('Estado de reserva desconocido: $valor');
    }
  }

  String get etiqueta {
    switch (this) {
      case EstadoReserva.pendiente:
        return 'Pendiente de preparación';
      case EstadoReserva.preparada:
        return 'Lista para tu visita';
      case EstadoReserva.enAtencion:
        return 'En atención';
      case EstadoReserva.listaParaCaja:
        return 'En proceso en sucursal';
      case EstadoReserva.atendida:
        return 'Atendida';
      case EstadoReserva.cancelada:
        return 'Cancelada';
      case EstadoReserva.vencida:
        return 'Vencida';
    }
  }
}

class ReservaDetalleOut {
  const ReservaDetalleOut({
    required this.id,
    required this.producto,
    required this.variante,
    required this.cantidad,
    required this.estado,
  });

  final int id;
  final ProductoResumen producto;
  final VarianteResumen variante;
  final int cantidad;
  final EstadoReserva estado;

  factory ReservaDetalleOut.fromJson(Map<String, dynamic> json) {
    return ReservaDetalleOut(
      id: json['id'] as int,
      producto: ProductoResumen.fromJson(json['producto'] as Map<String, dynamic>),
      variante: VarianteResumen.fromJson(json['variante'] as Map<String, dynamic>),
      cantidad: json['cantidad'] as int,
      estado: EstadoReserva.fromJson(json['estado'] as String),
    );
  }
}

class ReservaOut {
  const ReservaOut({
    required this.id,
    required this.codigoReserva,
    required this.sucursal,
    required this.estadoGeneral,
    required this.fechaReserva,
    required this.horaInicio,
    required this.horaFin,
    required this.fechaCreacion,
    required this.detalles,
  });

  final int id;
  // Identificador visible para el Cliente (ej. "RS-00025") -- se muestra
  // siempre en vez del `id` interno.
  final String codigoReserva;
  final SucursalResumen sucursal;
  final EstadoReserva estadoGeneral;
  final String fechaReserva; // "YYYY-MM-DD"
  final String horaInicio; // "HH:MM:SS"
  final String horaFin; // "HH:MM:SS"
  final String fechaCreacion; // ISO 8601 con offset
  final List<ReservaDetalleOut> detalles;

  factory ReservaOut.fromJson(Map<String, dynamic> json) {
    return ReservaOut(
      id: json['id'] as int,
      codigoReserva: json['codigo_reserva'] as String,
      sucursal: SucursalResumen.fromJson(json['sucursal'] as Map<String, dynamic>),
      estadoGeneral: EstadoReserva.fromJson(json['estado_general'] as String),
      fechaReserva: json['fecha_reserva'] as String,
      horaInicio: json['hora_inicio'] as String,
      horaFin: json['hora_fin'] as String,
      fechaCreacion: json['fecha_creacion'] as String,
      detalles: (json['detalles'] as List)
          .map((item) => ReservaDetalleOut.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
