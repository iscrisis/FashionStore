import 'package:flutter/material.dart';

/// Los 4 landmarks CRUDOS (hombro izq/der, cadera izq/der) que arma el
/// torso, en el MISMO espacio de [TorsoPose.tamanoFrame]. Nunca se usan
/// para nada más (ni identidad, ni medidas, ni análisis corporal).
@immutable
class PuntosTorso {
  const PuntosTorso({
    required this.hombroIzquierdo,
    required this.hombroDerecho,
    required this.caderaIzquierda,
    required this.caderaDerecha,
  });

  final Offset hombroIzquierdo;
  final Offset hombroDerecho;
  final Offset caderaIzquierda;
  final Offset caderaDerecha;
}

/// Resultado MÍNIMO de la detección de pose que necesita el vestidor
/// virtual: solo la ubicación aproximada del torso -- NUNCA identidad,
/// análisis corporal, mediciones reales ni nada que se guarde o
/// reutilice fuera de esta pantalla (ver `PoseTrackerService`).
///
/// A PROPÓSITO no está normalizado a 0..1: [centro]/[anchoHombros]/
/// [puntos] están en PÍXELES tal cual los entrega ML Kit, solo con un
/// espejo horizontal (ver `PoseTrackerService._espejarPunto`; NO se
/// rotan -- ML Kit ya los devuelve correctamente ubicados una vez que se
/// le pasa la rotación en `InputImageMetadata`), junto con [tamanoFrame]
/// (ver `PoseTrackerService._tamanoFrameRotado`: ancho/alto
/// INTERCAMBIADOS respecto al buffer crudo, para que coincida con la
/// proporción que usa `CameraPreview` -- ese widget muestra el video
/// dentro de una caja con la proporción invertida, ver su docstring).
/// Mezclar un valor normalizado al frame
/// con el tamaño real del widget fue justamente el bug que rompía el
/// posicionamiento (`BoxFit.cover` recorta el frame para llenar el
/// widget, así que "la mitad del frame" no es lo mismo que "la mitad
/// del widget" salvo que compartan la misma proporción). Por eso la
/// conversión a coordenadas de pantalla vive en UNA sola función,
/// `transformPosePointToScreen` (`pose_coordinate_transformer.dart`),
/// que sí conoce el tamaño del widget -- esta clase no lo necesita.
@immutable
class TorsoPose {
  const TorsoPose({
    required this.centro,
    required this.anchoHombros,
    required this.tamanoFrame,
    required this.puntos,
  });

  /// Centro horizontal = punto medio ENTRE HOMBROS; centro vertical =
  /// promedio de hombros y caderas -- en píxeles del frame rotado.
  final Offset centro;

  /// Distancia hombro-a-hombro (`shoulderDistance`), en píxeles del
  /// mismo frame rotado -- NUNCA la distancia de caderas ni ningún otro
  /// landmark. Se usa ÚNICAMENTE para escalar la prenda: nunca se
  /// expone como una medida corporal real, no se persiste, no se
  /// compara entre sesiones ni se usa para recomendar talla.
  final double anchoHombros;

  /// Tamaño del frame de cámara YA ROTADO (mismo espacio que [centro] y
  /// [puntos]), necesario para `transformPosePointToScreen`.
  final Size tamanoFrame;

  /// Los 4 landmarks individuales -- ver `PuntosTorso`.
  final PuntosTorso puntos;
}
