import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/services.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';

import '../models/torso_pose.dart';

/// Envuelve `PoseDetector` de Google ML Kit -- TODO el procesamiento
/// ocurre EN EL DISPOSITIVO (sin red, sin servicios externos). Expone
/// ÚNICAMENTE `TorsoPose` (centro + ancho del torso, ver ese archivo),
/// calculado a partir de EXACTAMENTE 4 landmarks: hombro izquierdo/
/// derecho y cadera izquierda/derecha. Nunca nariz, ojos, muñecas,
/// tobillos ni ningún "centro general del cuerpo" que ML Kit pudiera
/// exponer -- para una blusa, lo único relevante es el torso. Nunca hace
/// reconocimiento de identidad, análisis corporal, mediciones reales ni
/// recomendaciones de talla -- eso no es parte de este caso de uso.
///
/// Esta clase se detiene en "rotar el landmark a orientación de
/// pantalla, en píxeles del frame" -- NUNCA normaliza a 0..1 ni conoce
/// el tamaño del widget de Flutter. Ese último paso (que depende de
/// cómo `CameraView` recorta/escala el preview con `BoxFit.cover`) es
/// responsabilidad exclusiva de `transformPosePointToScreen`
/// (`pose_coordinate_transformer.dart`) -- mezclar ambos pasos fue
/// justamente el bug que rompía el posicionamiento.
class PoseTrackerService {
  PoseTrackerService()
    : _detector = PoseDetector(options: PoseDetectorOptions(mode: PoseDetectionMode.stream));

  final PoseDetector _detector;

  // Evita encolar frames: mientras ML Kit todavía procesa uno, los
  // nuevos se descartan en vez de acumularse -- patrón estándar para
  // cámara en stream + ML Kit, así la app no se atrasa ni acumula
  // memoria si el dispositivo es lento (prioridad: estabilidad antes
  // que precisión).
  bool _procesando = false;

  // Último torso YA suavizado (ver `_suavizar`) -- se conserva entre
  // frames para: (a) el suavizado exponencial, y (b) para que un frame
  // sin detección utilizable no tenga que "adivinar" nada, ver
  // `procesarFrame`: simplemente no se actualiza y quien llama
  // (`CameraView` → `VestidorVirtualPage`) conserva la última posición
  // válida, tal como pide el CU.
  TorsoPose? _ultimoTorso;

  // Interpolación simple (no un filtro de Kalman ni nada más
  // sofisticado, a propósito): cada posición nueva se acerca un
  // porcentaje hacia el valor recién detectado, así un frame ruidoso no
  // hace saltar la prenda de golpe -- "no se requiere precisión
  // perfecta", pero sí estabilidad.
  //
  // Empezó en 0.2 (20% por frame); confirmado en dispositivo real que
  // con ese valor la prenda se notaba "atrasada" respecto al cuerpo al
  // acercarse/alejarse de la cámara -- CUALQUIER suavizado exponencial
  // atrasa proporcionalmente a qué tan rápido cambia el valor real, y
  // 0.2 era demasiado lento para un movimiento normal frente al espejo.
  // 0.45 sigue absorbiendo el ruido de un frame puntual (que es lo único
  // que este suavizado necesita cubrir -- la posición en sí ya fue
  // auditada y es correcta) sin el retraso perceptible del valor
  // anterior.
  static const double _factorSuavizado = 0.45;

  static const _confianzaMinima = 0.4;

  static const Map<DeviceOrientation, int> _gradosPorOrientacion = {
    DeviceOrientation.portraitUp: 0,
    DeviceOrientation.landscapeLeft: 90,
    DeviceOrientation.portraitDown: 180,
    DeviceOrientation.landscapeRight: 270,
  };

  /// Procesa UN frame de la cámara y devuelve el torso detectado
  /// (ya suavizado), o `null` si no hay ninguna persona/hombros/caderas
  /// visibles con suficiente confianza, si la plataforma/formato del
  /// frame no es compatible, o si ML Kit falla por cualquier motivo --
  /// SIEMPRE `null` en vez de lanzar una excepción o devolver (0,0):
  /// quien llama ya sabe simplemente CONSERVAR la última posición válida
  /// que tenía.
  Future<TorsoPose?> procesarFrame({
    required CameraImage image,
    required CameraDescription camara,
    required DeviceOrientation orientacionDispositivo,
  }) async {
    if (_procesando) return null;
    _procesando = true;
    try {
      final inputImage = _construirInputImage(image, camara, orientacionDispositivo);
      final metadata = inputImage?.metadata;
      if (inputImage == null || metadata == null) return null;
      if (metadata.size.width <= 0 || metadata.size.height <= 0) return null;

      final poses = await _detector.processImage(inputImage);
      if (poses.isEmpty) return null;

      return _torsoDe(poses.first, metadata);
    } catch (_) {
      return null;
    } finally {
      _procesando = false;
    }
  }

  /// Construye el `InputImage` que pide ML Kit a partir del frame crudo
  /// de `camera`. Solo se admite el formato de UN plano por cámara
  /// (`nv21` en Android, `bgra8888` en iOS -- ver `CameraView`, que pide
  /// exactamente ese `imageFormatGroup` al inicializar el controlador);
  /// cualquier otra cosa devuelve `null` en vez de intentar adivinar.
  InputImage? _construirInputImage(
    CameraImage image,
    CameraDescription camara,
    DeviceOrientation orientacionDispositivo,
  ) {
    final rotation = _rotacionDe(camara, orientacionDispositivo);
    if (rotation == null) return null;

    final rawFormat = image.format.raw;
    if (rawFormat is! int) return null;
    final format = InputImageFormatValue.fromRawValue(rawFormat);
    if (format == null) return null;
    if (Platform.isAndroid && format != InputImageFormat.nv21) return null;
    if (Platform.isIOS && format != InputImageFormat.bgra8888) return null;
    if (image.planes.length != 1) return null;

    final plane = image.planes.first;
    return InputImage.fromBytes(
      bytes: plane.bytes,
      metadata: InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: rotation,
        format: format,
        bytesPerRow: plane.bytesPerRow,
      ),
    );
  }

  /// Combina la orientación física del sensor (`sensorOrientation`, fija
  /// por cámara) con la orientación actual del dispositivo -- mismo
  /// cálculo documentado por Google ML Kit para integrarse con el
  /// paquete `camera`. En iOS, AVFoundation ya resuelve la orientación
  /// de la conexión de captura, así que alcanza con `sensorOrientation`.
  InputImageRotation? _rotacionDe(CameraDescription camara, DeviceOrientation orientacionDispositivo) {
    if (Platform.isIOS) {
      return InputImageRotationValue.fromRawValue(camara.sensorOrientation);
    }
    if (!Platform.isAndroid) return null;

    final gradosDispositivo = _gradosPorOrientacion[orientacionDispositivo];
    if (gradosDispositivo == null) return null;

    final int gradosFinal;
    if (camara.lensDirection == CameraLensDirection.front) {
      gradosFinal = (camara.sensorOrientation + gradosDispositivo) % 360;
    } else {
      gradosFinal = (camara.sensorOrientation - gradosDispositivo + 360) % 360;
    }
    return InputImageRotationValue.fromRawValue(gradosFinal);
  }

  /// Devuelve el landmark tal como lo entrega ML Kit, con UN solo ajuste:
  /// espejo horizontal (`anchoBuffer - x`) -- ver docstring de
  /// [_tamanoFrameRotado] para la auditoría que confirmó que ML Kit ya
  /// no necesita ninguna rotación manual (ver historial de este método:
  /// antes rotaba 90°/180°/270°, eso era la "rotación aplicada dos
  /// veces").
  ///
  /// El espejo SÍ hace falta y es intencional: confirmado en dispositivo
  /// que, sin él, mover el cuerpo hacia la derecha del Cliente movía el
  /// punto hacia la IZQUIERDA en pantalla -- la cámara frontal entrega
  /// el buffer "como te ve ella" (sin espejar), pero un vestidor virtual
  /// debe comportarse como un espejo real (mover tu mano derecha la
  /// mueve hacia donde VOS sentís que es tu derecha en pantalla). Debe
  /// aplicarse en el MISMO sentido que el espejo visual de
  /// `CameraPreview` (ver `CameraView.build`) para que el punto de ML
  /// Kit siga cayendo sobre el cuerpo que se ve en pantalla.
  Offset _espejarPunto(double x, double y, InputImageMetadata metadata) => Offset(metadata.size.width - x, y);

  /// Tamaño de referencia para `transformPosePointToScreen` -- ancho/alto
  /// INTERCAMBIADOS (nunca los del buffer crudo tal cual) para que el
  /// "cover" de los puntos recorte con la MISMA proporción que usa
  /// `CameraPreview` para el video: ese widget (paquete `camera`, ver
  /// `camera_preview.dart`) envuelve el preview en
  /// `AspectRatio(1 / controller.value.aspectRatio)` para portrait --
  /// es decir, mid buffer crudo (720x480, ancho:alto = 1.5) se muestra
  /// en una caja de proporción INVERSA (≈480:720). Sin este intercambio,
  /// los puntos calculaban su recorte con la proporción del buffer
  /// crudo, MUY distinta a la del video -- correcto en orden relativo
  /// (por eso la prueba de calibración, que no tiene video de fondo, se
  /// veía bien) pero con una escala/recorte completamente distinta al
  /// video real, produciendo el desajuste reportado ("nariz en la
  /// axila", "hombro a la mitad de la panza"). Los PUNTOS en sí (ver
  /// [_espejarPunto]) NO se tocan acá -- esto solo cambia la escala, no
  /// el orden de los ejes (ver commit anterior: intercambiar ahí SÍ
  /// rompía el orden izquierda/derecha).
  Size _tamanoFrameRotado(InputImageMetadata metadata) {
    final anchoBuffer = metadata.size.width;
    final altoBuffer = metadata.size.height;
    final rotado90 =
        metadata.rotation == InputImageRotation.rotation90deg ||
        metadata.rotation == InputImageRotation.rotation270deg;
    return rotado90 ? Size(altoBuffer, anchoBuffer) : Size(anchoBuffer, altoBuffer);
  }

  /// Calcula el torso a partir de EXACTAMENTE 4 landmarks (hombro
  /// izq/der, cadera izq/der) y aplica el suavizado exponencial.
  /// Devuelve `null` si falta cualquiera de los 4 o su confianza es muy
  /// baja -- los hombros se validan PRIMERO porque son el par crítico
  /// para una blusa (sin ambos hombros no hay de dónde "colgarla"); las
  /// caderas solo aportan el límite inferior del torso para el centro
  /// vertical. No exige una pose perfecta de frente ("no se requiere
  /// precisión perfecta", ver CU).
  TorsoPose? _torsoDe(Pose pose, InputImageMetadata metadata) {
    // "Izq"/"Der" acá son el anatómico de ML Kit tal cual -- con el
    // espejo de coordenadas ya aplicado en [_espejarPunto], el lado
    // anatómico real de la persona YA coincide con el lado que el
    // Cliente siente como suyo en pantalla (confirmado en dispositivo:
    // levantar la mano izquierda real mueve el punto `leftWrist` hacia
    // el lado izquierdo visual). Invertir TAMBIÉN la etiqueta -- como
    // hacía una versión anterior de este método -- era el error: dejaba
    // la posición bien pero el cartel cruzado.
    final hombroIzq = pose.landmarks[PoseLandmarkType.leftShoulder];
    final hombroDer = pose.landmarks[PoseLandmarkType.rightShoulder];
    if (hombroIzq == null || hombroDer == null) return null;
    if (hombroIzq.likelihood < _confianzaMinima || hombroDer.likelihood < _confianzaMinima) return null;

    final caderaIzq = pose.landmarks[PoseLandmarkType.leftHip];
    final caderaDer = pose.landmarks[PoseLandmarkType.rightHip];
    if (caderaIzq == null || caderaDer == null) return null;
    if (caderaIzq.likelihood < _confianzaMinima || caderaDer.likelihood < _confianzaMinima) return null;

    final hIzq = _espejarPunto(hombroIzq.x, hombroIzq.y, metadata);
    final hDer = _espejarPunto(hombroDer.x, hombroDer.y, metadata);
    final cIzq = _espejarPunto(caderaIzq.x, caderaIzq.y, metadata);
    final cDer = _espejarPunto(caderaDer.x, caderaDer.y, metadata);

    // Centro horizontal: SOLO hombros -- una blusa cuelga del torso
    // superior, las caderas no deben influir en su centrado horizontal.
    final centerX = (hIzq.dx + hDer.dx) / 2;
    // Centro vertical: hombros + caderas, para ubicar el torso completo
    // (de hombros a cadera), tal como pide el CU.
    final centerY = (hIzq.dy + hDer.dy + cIzq.dy + cDer.dy) / 4;
    // Ancho del torso: distancia SOLO entre hombros -- es lo único que
    // se usa para escalar la prenda, nunca la distancia de caderas.
    final shoulderDistance = (hIzq.dx - hDer.dx).abs();

    final crudo = TorsoPose(
      centro: Offset(centerX, centerY),
      anchoHombros: shoulderDistance,
      tamanoFrame: _tamanoFrameRotado(metadata),
      puntos: PuntosTorso(
        hombroIzquierdo: hIzq,
        hombroDerecho: hDer,
        caderaIzquierda: cIzq,
        caderaDerecha: cDer,
      ),
    );

    return _suavizar(crudo);
  }

  /// Suavizado exponencial simple: `anterior + factor * (nuevo -
  /// anterior)`, aplicado a cada punto por igual. La primera detección
  /// de la sesión no tiene "anterior" -- se usa tal cual, sin blend,
  /// para no arrancar con un valor artificialmente amortiguado.
  TorsoPose _suavizar(TorsoPose nuevo) {
    final anterior = _ultimoTorso;
    if (anterior == null) {
      _ultimoTorso = nuevo;
      return nuevo;
    }

    Offset mezclar(Offset a, Offset b) => a + (b - a) * _factorSuavizado;

    final suavizado = TorsoPose(
      centro: mezclar(anterior.centro, nuevo.centro),
      anchoHombros: anterior.anchoHombros + (nuevo.anchoHombros - anterior.anchoHombros) * _factorSuavizado,
      tamanoFrame: nuevo.tamanoFrame,
      puntos: PuntosTorso(
        hombroIzquierdo: mezclar(anterior.puntos.hombroIzquierdo, nuevo.puntos.hombroIzquierdo),
        hombroDerecho: mezclar(anterior.puntos.hombroDerecho, nuevo.puntos.hombroDerecho),
        caderaIzquierda: mezclar(anterior.puntos.caderaIzquierda, nuevo.puntos.caderaIzquierda),
        caderaDerecha: mezclar(anterior.puntos.caderaDerecha, nuevo.puntos.caderaDerecha),
      ),
    );
    _ultimoTorso = suavizado;
    return suavizado;
  }

  /// Libera los recursos nativos del detector -- se llama desde
  /// `CameraView.dispose()`, igual que se libera la cámara.
  Future<void> close() => _detector.close();
}
