/// Refleja `ColeccionDestacadaPublicaOut`
/// (CU10_GestionarTemporadasColecciones/schemas.py) -- deliberadamente solo
/// trae id + imagen ("sin datos administrativos"). El nombre real se
/// resuelve por separado cruzando este id contra /catalogo/colecciones.
class ColeccionDestacada {
  const ColeccionDestacada({required this.id, this.imagenDestacadaUrl});

  final int id;
  final String? imagenDestacadaUrl;

  factory ColeccionDestacada.fromJson(Map<String, dynamic> json) {
    return ColeccionDestacada(
      id: json['id'] as int,
      imagenDestacadaUrl: json['imagen_destacada_url'] as String?,
    );
  }
}
