import 'dart:math' as math;
import 'dart:ui';

/// ÚNICA función responsable de convertir un punto en el espacio del
/// frame de cámara (ya rotado a orientación de pantalla, en píxeles --
/// ver `TorsoPose`/`PoseTrackerService`) a la coordenada REAL donde ese
/// punto se ve dentro del widget de Flutter que muestra la cámara.
/// Ningún widget debe reimplementar esta cuenta por su cuenta -- todos
/// usan esta función, nunca una versión propia.
///
/// Es necesaria porque `CameraView` dibuja el preview con
/// `BoxFit.cover`: ESCALA el frame hasta cubrir todo el widget y
/// RECORTA (centrado) lo que sobra en el eje más ancho -- nunca lo
/// deforma. Esa era la causa raíz del posicionamiento roto: se estaba
/// tratando una fracción 0..1 DEL FRAME como si fuera directamente una
/// fracción 0..1 DEL WIDGET (vía `Alignment`), lo cual solo es correcto
/// si frame y widget comparten exactamente la misma proporción -- algo
/// que casi nunca pasa entre una cámara (p. ej. 480x720) y la pantalla
/// de un teléfono (p. ej. 1080x2400). Cualquier punto que no esté
/// exactamente en el centro terminaba desplazado, y el desplazamiento
/// crecía cuanto más lejos del centro estuviera el punto -- exactamente
/// el síntoma reportado ("posiciones aleatorias", "esquinas",
/// "movimientos contradictorios").
///
/// [puntoFrame] -- el punto devuelto por ML Kit, YA ROTADO a
/// orientación de pantalla (ver `PoseTrackerService`), en píxeles.
/// [tamanoFrame] -- ancho/alto de ESE frame ya rotado.
/// [tamanoWidget] -- ancho/alto REAL del widget en pantalla (obtenido
/// con `LayoutBuilder`, nunca asumido).
Offset transformPosePointToScreen({
  required Offset puntoFrame,
  required Size tamanoFrame,
  required Size tamanoWidget,
}) {
  if (tamanoFrame.width <= 0 || tamanoFrame.height <= 0) return Offset.zero;

  final escala = _escalaCover(tamanoFrame, tamanoWidget);
  final anchoEscalado = tamanoFrame.width * escala;
  final altoEscalado = tamanoFrame.height * escala;

  // `BoxFit.cover` centra el recorte -- este offset puede ser negativo
  // (representa lo que queda fuera de pantalla a cada lado del eje que
  // se recorta).
  final offsetX = (tamanoWidget.width - anchoEscalado) / 2 + tamanoWidget.width * _correccionOffsetXFraccion;
  final offsetY = (tamanoWidget.height - altoEscalado) / 2 + tamanoWidget.height * _correccionOffsetYFraccion;

  return Offset(puntoFrame.dx * escala + offsetX, puntoFrame.dy * escala + offsetY);
}

/// Corrección empírica TEMPORAL, calibrada en dispositivo real (ver
/// auditoría del CU "Vestidor Virtual") comparando en vivo, contra el
/// cuerpo visible en el video, dónde caía `LEFT_SHOULDER`/
/// `RIGHT_SHOULDER` calculados vs dónde estaban realmente -- ambos se
/// desplazaban la MISMA distancia (confirmado moviendo un slider de
/// traslación con la persona centrada), lo que descarta un problema de
/// escala o de ejes y confirma una traslación constante: el buffer que
/// usa ML Kit (`ImageAnalysis`) y el que muestra `CameraPreview`
/// (`Preview`), aunque reportan la MISMA resolución, no recortan
/// exactamente el mismo campo de visión del sensor -- CameraX no
/// garantiza que ambos "use cases" compartan encuadre solo por pedir la
/// misma resolución.
///
/// Expresada como FRACCIÓN del ancho/alto del widget (nunca píxeles
/// fijos) para que escale con el tamaño de pantalla de cualquier
/// dispositivo, no solo el usado para calibrar. Si se prueba en un
/// dispositivo distinto y el desajuste vuelve a aparecer, hay que
/// recalibrar (comparar en vivo, contra el cuerpo real, dónde caen
/// `LEFT_SHOULDER`/`RIGHT_SHOULDER`) y actualizar estas dos constantes.
///
/// AJUSTE POSTERIOR (X): re-calculando el offset exacto (regresión con
/// 2 puntos) sobre CADA prueba posterior a la calibración inicial --
/// hombros a distancia normal, caderas, y el caso extremo cercano --
/// dio de forma consistente ~-316/-317 (contra los -315.55 originales),
/// lo que confirma que la fórmula en sí es estable y no depende de la
/// distancia a la cámara. Pero el Cliente, ya con el offset aplicado,
/// reportó la prenda corrida "como medio hombro" hacia su izquierda
/// incluso bien posicionado -- promediando la distancia real medida
/// (centro de hombros vs centro del widget) en esas pruebas, ~9-10% del
/// ancho del widget, se suma acá como corrección adicional hacia la
/// derecha (el centro del cuerpo, tal como lo entrega `ImageAnalysis`,
/// no coincide exactamente con el centro geométrico de lo que
/// `CameraPreview` muestra).
const double _correccionOffsetXFraccion = -0.58;
const double _correccionOffsetYFraccion = -0.015;

/// Variante de conveniencia para una DISTANCIA (p. ej. `shoulderDistance`
/// para escalar la prenda) en vez de un punto: se escala por el mismo
/// factor que usa `transformPosePointToScreen`, sin desplazamiento (el
/// centrado del recorte no aplica a una distancia, solo a una
/// posición).
double transformPoseDistanceToScreen({
  required double distanciaFrame,
  required Size tamanoFrame,
  required Size tamanoWidget,
}) {
  if (tamanoFrame.width <= 0 || tamanoFrame.height <= 0) return 0;
  return distanciaFrame * _escalaCover(tamanoFrame, tamanoWidget);
}

double _escalaCover(Size tamanoFrame, Size tamanoWidget) {
  return math.max(tamanoWidget.width / tamanoFrame.width, tamanoWidget.height / tamanoFrame.height);
}
