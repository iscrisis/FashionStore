import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/asistente_ia/models/mensaje_asistente.dart';

// JSON real capturado de POST /api/v1/asistente-ia/mensaje en producción
// para el mensaje "tienes ropa en negro?" -- reproduce el bug reportado
// (Flutter mostraba solo el mensaje de error genérico, sin productos, por
// un timeout de 10s del ApiClient demasiado corto para CU29). Este test
// prueba que, una vez que el JSON SÍ llega, MensajeAsistenteResponse lo
// parsea completo -- ningún campo se ignora.
const _respuestaRealBackend = '''
{
  "respuesta": "Estas son algunas opciones que encontré: Abrigo color, Abrigo conf, Cangurera. Encontré más opciones en el catálogo.",
  "productos": [
    {
      "id": 1435,
      "nombre": "Abrigo color",
      "imagen_principal_url": "https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/27539fc4b43c4bc68e473e2658790e32.jpg",
      "precio_base": 25.0,
      "precio_final": 25.0,
      "en_promocion": false,
      "porcentaje_descuento": null,
      "color": null,
      "talla": null,
      "disponibilidad_resumen": "Disponible en Mall ventura."
    },
    {
      "id": 467,
      "nombre": "Abrigo conf",
      "imagen_principal_url": "https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/359683ac435842e38ed4bbc94b1cbb41.jpg",
      "precio_base": 250.0,
      "precio_final": 250.0,
      "en_promocion": false,
      "porcentaje_descuento": null,
      "color": "Negro",
      "talla": null,
      "disponibilidad_resumen": "Sin stock disponible por el momento."
    },
    {
      "id": 854,
      "nombre": "Cangurera",
      "imagen_principal_url": "https://rg0v9g13atk7iohx.public.blob.vercel-storage.com/productos/8bf32d210c1048d7897d62be2c0c7882.jpg",
      "precio_base": 100.0,
      "precio_final": 100.0,
      "en_promocion": false,
      "porcentaje_descuento": null,
      "color": "Negro",
      "talla": null,
      "disponibilidad_resumen": "Sin stock disponible por el momento."
    }
  ],
  "tipo": "recomendacion",
  "hay_mas_resultados": true
}
''';

void main() {
  test('MensajeAsistenteResponse.fromJson parsea texto, productos y flags completos', () {
    final json = jsonDecode(_respuestaRealBackend) as Map<String, dynamic>;
    final respuesta = MensajeAsistenteResponse.fromJson(json);

    expect(respuesta.respuesta, contains('Abrigo color'));
    expect(respuesta.tipo, 'recomendacion');
    expect(respuesta.hayMasResultados, isTrue);
    expect(respuesta.productos, hasLength(3));

    final conColor = respuesta.productos.firstWhere((p) => p.id == 467);
    expect(conColor.nombre, 'Abrigo conf');
    expect(conColor.color, 'Negro');
    expect(conColor.precioFinal, 250.0);
    expect(conColor.imagenPrincipalUrl, isNotNull);
    expect(conColor.disponibilidadResumen, 'Sin stock disponible por el momento.');

    final sinColor = respuesta.productos.firstWhere((p) => p.id == 1435);
    expect(sinColor.color, isNull);
    expect(sinColor.porcentajeDescuento, isNull);
  });
}
