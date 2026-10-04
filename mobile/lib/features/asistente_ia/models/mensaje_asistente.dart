// Modelo de CU29 -- Obtener recomendaciones mediante IA (Cliente/Invitado).
// Refleja 1:1 el contrato de
// backend/modules/P6_InnovacionYAnalisis/CU29_ObtenerRecomendacionesIA/schemas.py
// -- el mismo JSON que ya consume Angular (ver
// frontend/web/.../asistente-ia/asistente-ia.model.ts). Flutter NUNCA llama
// a Gemini directamente, solo a POST /asistente-ia/mensaje (ver
// asistente_ia_service.dart). El historial de la conversación vive SOLO en
// memoria de este State (ver widgets/asistente_ia_overlay.dart) -- se pierde
// si se cierra la app, igual que en la web.

enum RolMensajeChat {
  usuario,
  asistente;

  String get valor => this == RolMensajeChat.usuario ? 'usuario' : 'asistente';
}

class TurnoChat {
  const TurnoChat({required this.rol, required this.texto});

  final RolMensajeChat rol;
  final String texto;

  Map<String, dynamic> toJson() => {'rol': rol.valor, 'texto': texto};
}

/// Un producto REAL (ya verificado contra PostgreSQL por el backend) que el
/// asistente muestra dentro del chat. precio_base/precio_final/en_promocion/
/// porcentaje_descuento SIEMPRE vienen ya calculados por FastAPI (CU32) --
/// Flutter nunca los recalcula, solo los muestra.
class ProductoRecomendado {
  const ProductoRecomendado({
    required this.id,
    required this.nombre,
    required this.precioBase,
    required this.precioFinal,
    required this.enPromocion,
    this.imagenPrincipalUrl,
    this.porcentajeDescuento,
    this.color,
    this.talla,
    this.disponibilidadResumen,
  });

  final int id;
  final String nombre;
  final String? imagenPrincipalUrl;
  final double precioBase;
  final double precioFinal;
  final bool enPromocion;
  final double? porcentajeDescuento;
  final String? color;
  final String? talla;
  final String? disponibilidadResumen;

  factory ProductoRecomendado.fromJson(Map<String, dynamic> json) {
    return ProductoRecomendado(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      imagenPrincipalUrl: json['imagen_principal_url'] as String?,
      precioBase: (json['precio_base'] as num).toDouble(),
      precioFinal: (json['precio_final'] as num).toDouble(),
      enPromocion: json['en_promocion'] as bool,
      porcentajeDescuento: (json['porcentaje_descuento'] as num?)?.toDouble(),
      color: json['color'] as String?,
      talla: json['talla'] as String?,
      disponibilidadResumen: json['disponibilidad_resumen'] as String?,
    );
  }
}

class MensajeAsistenteResponse {
  const MensajeAsistenteResponse({
    required this.respuesta,
    required this.productos,
    required this.tipo,
    required this.hayMasResultados,
  });

  final String respuesta;
  final List<ProductoRecomendado> productos;
  final String tipo;
  final bool hayMasResultados;

  factory MensajeAsistenteResponse.fromJson(Map<String, dynamic> json) {
    return MensajeAsistenteResponse(
      respuesta: json['respuesta'] as String,
      productos: (json['productos'] as List)
          .map((item) => ProductoRecomendado.fromJson(item as Map<String, dynamic>))
          .toList(),
      tipo: json['tipo'] as String,
      hayMasResultados: json['hay_mas_resultados'] as bool,
    );
  }
}

/// Un mensaje ya renderizado en el chat -- superset de [TurnoChat] con los
/// productos que trajo esa respuesta del asistente (si los trajo).
class MensajeChat {
  const MensajeChat({required this.rol, required this.texto, this.productos});

  final RolMensajeChat rol;
  final String texto;
  final List<ProductoRecomendado>? productos;
}
