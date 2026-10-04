import 'dart:async';
import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show DeviceOrientation;

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_text_styles.dart';
import '../models/torso_pose.dart';
import '../services/pose_tracker_service.dart';

/// Vista de cámara en vivo del vestidor virtual. Encapsula TODO el ciclo de
/// vida de `CameraController` -- el paquete `camera` es quien dispara el
/// permiso nativo de cámara al llamar `initialize()` (no hace falta pedirlo
/// a mano ni agregar `permission_handler`), así que esta clase cubre sola
/// los pasos "Solicita permiso de cámara" + "Muestra cámara del
/// dispositivo" del flujo.
///
/// Además transmite cada frame a un `PoseTrackerService` (ML Kit Pose
/// Detection, on-device) para calcular la ubicación aproximada del
/// torso y notificarla vía [onTorsoDetectado] -- pero la detección es un
/// AGREGADO opcional: si no hay persona, hombros o caderas visibles, si
/// hay poca luz, o si el detector falla por cualquier motivo, este
/// widget simplemente no llama a [onTorsoDetectado] con un valor nuevo y
/// sigue mostrando la cámara con normalidad. Quien consume el callback
/// (`VestidorVirtualPage`) ya sabe conservar la última posición conocida
/// o caer a la posición manual/de categoría -- nunca pantalla vacía, sin
/// reconocimiento corporal más allá de esos 4 landmarks, sin IA
/// generativa, avatar 3D ni AR externo.
///
/// El `CameraPreview` se muestra SIN ningún `Transform.flip` propio --
/// `camera_android_camerax` ya espeja el preview de la cámara frontal
/// por su cuenta (comportamiento nativo del plugin, no de este widget),
/// así que lo que el Cliente ve YA se comporta como un espejo real
/// (mover el cuerpo hacia su derecha se ve moverse hacia donde ÉL siente
/// que es su derecha en pantalla). Agregar acá un volteo adicional
/// DUPLICA ese espejo y vuelve a invertir la imagen -- confirmado en
/// dispositivo real.
///
/// Las coordenadas que calcula ML Kit, en cambio, NO pasan por ese
/// pipeline de preview (vienen del `CameraImage` crudo, antes de
/// cualquier transformación visual de Flutter) y por lo tanto SÍ
/// necesitan su propio espejo manual -- ver
/// `PoseTrackerService._espejarPunto`. Es el único lugar que debe
/// espejar; ni este widget ni `transformPosePointToScreen` deben
/// agregar otro.
class CameraView extends StatefulWidget {
  const CameraView({super.key, this.onTorsoDetectado});

  /// Se invoca con la pose detectada en un frame, o `null` cuando ese
  /// frame no produjo ninguna detección utilizable. `null` NO significa
  /// "error" -- puede ser simplemente que nadie está frente a la cámara
  /// todavía.
  final ValueChanged<TorsoPose?>? onTorsoDetectado;

  @override
  State<CameraView> createState() => _CameraViewState();
}

class _CameraViewState extends State<CameraView> with WidgetsBindingObserver {
  CameraController? _controller;
  String? _error;
  final _poseTracker = PoseTrackerService();

  // `controller.value.previewSize` puede no estar listo todavía justo
  // después de `initialize()` (con `camera_android_camerax` se completa
  // un instante después, cuando la superficie del preview ya está
  // produciendo frames) -- este listener lo cachea apenas aparece, para
  // que `build()` siempre tenga el valor real en vez de depender de en
  // qué momento exacto llegó el primer frame.
  Size? _previewSize;

  void _onControllerValueChanged() {
    final nuevoTamano = _controller?.value.previewSize;
    if (nuevoTamano != null && nuevoTamano != _previewSize) {
      setState(() => _previewSize = nuevoTamano);
    }
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _iniciarCamara();
  }

  Future<void> _iniciarCamara() async {
    try {
      final camaras = await availableCameras();
      if (camaras.isEmpty) {
        if (!mounted) return;
        setState(() => _error = 'Este dispositivo no tiene una cámara disponible.');
        return;
      }
      final camaraFrontal = camaras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => camaras.first,
      );
      final controller = CameraController(
        camaraFrontal,
        ResolutionPreset.medium,
        enableAudio: false,
        // Formato de un solo plano que ML Kit puede leer directo (NV21
        // en Android, BGRA en iOS) -- evita concatenar manualmente los
        // planos Y/U/V de YUV420, más simple y estable.
        imageFormatGroup: Platform.isAndroid ? ImageFormatGroup.nv21 : ImageFormatGroup.bgra8888,
      );
      await controller.initialize();
      if (!mounted) {
        await controller.dispose();
        return;
      }
      controller.addListener(_onControllerValueChanged);
      setState(() {
        _controller = controller;
        _previewSize = controller.value.previewSize;
        _error = null;
      });
      // Si el stream de imágenes falla al iniciar (dispositivo sin
      // soporte, etc.), el preview de cámara ya quedó andando arriba --
      // solo se pierde el ajuste automático de la prenda, nunca la
      // pantalla completa.
      try {
        await controller.startImageStream(_procesarFrame);
      } catch (_) {
        // Silencioso a propósito -- ver docstring de la clase.
      }
    } catch (_) {
      // Cubre tanto "permiso de cámara denegado" como cualquier otro fallo
      // de hardware -- en ambos casos no hay nada que el vestidor pueda
      // hacer más que informar y dejar que el Cliente vuelva al producto.
      if (!mounted) return;
      setState(() => _error = 'No se pudo acceder a la cámara. Revisa los permisos en Ajustes.');
    }
  }

  // `VestidorVirtualPage` bloquea la pantalla a portrait (ver su
  // `initState`) precisamente para que este valor sea siempre el
  // correcto -- CAUSA RAÍZ auditada del bug de landmarks rotados: leer
  // `controller.value.deviceOrientation` en vivo resultaba inestable
  // durante el arranque del stream de imágenes en `camera_android_camerax`
  // (reportaba una orientación transitoria distinta a portrait incluso
  // con el teléfono físicamente vertical), sumando un 90°/270° incorrecto
  // a `PoseTrackerService._rotacionDe`. Con la pantalla bloqueada, no hay
  // ninguna orientación real que "leer": siempre es esta.
  static const _orientacionDispositivo = DeviceOrientation.portraitUp;

  void _procesarFrame(CameraImage image) {
    final controller = _controller;
    if (controller == null || !mounted) return;
    unawaited(
      _poseTracker
          .procesarFrame(
            image: image,
            camara: controller.description,
            orientacionDispositivo: _orientacionDispositivo,
          )
          .then((torso) {
            if (!mounted) return;
            widget.onTorsoDetectado?.call(torso);
          }),
    );
  }

  Future<void> _detenerCamara() async {
    final controller = _controller;
    _controller = null;
    if (controller == null) return;
    controller.removeListener(_onControllerValueChanged);
    try {
      if (controller.value.isStreamingImages) {
        await controller.stopImageStream();
      }
    } catch (_) {
      // Ver docstring de la clase -- nunca debe tumbar la pantalla.
    }
    await controller.dispose();
  }

  /// FASE 4 -- liberar la cámara correctamente cuando la app pierde foco
  /// (el usuario abre notificaciones, cambia de app, bloquea la
  /// pantalla) y restaurarla al volver. `inactive` YA cubre el caso de
  /// pantalla bloqueada/centro de notificaciones en Android e iOS (el
  /// framework lo dispara antes que `paused`).
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) return;
    if (state == AppLifecycleState.inactive || state == AppLifecycleState.paused) {
      unawaited(_detenerCamara());
    } else if (state == AppLifecycleState.resumed) {
      _iniciarCamara();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_detenerCamara());
    unawaited(_poseTracker.close());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final error = _error;
    if (error != null) {
      return _CameraMensaje(mensaje: error);
    }

    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) {
      return const Center(
        child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.burgundy),
      );
    }

    final preview = SizedBox(
      width: _previewSize?.height ?? 1,
      height: _previewSize?.width ?? 1,
      child: CameraPreview(controller),
    );

    // SIN `Transform.flip` acá -- confirmado en dispositivo real que
    // agregarlo DUPLICABA el espejo: `camera_android_camerax` ya espeja
    // el preview de la cámara frontal por su cuenta (ver
    // `image_reader_rotated_preview.dart` del plugin: "if the camera is
    // front facing... mirror the camera preview"), así que el preview
    // que llega acá YA se ve como espejo real. El único espejo que hace
    // falta agregar a mano es el de las coordenadas de ML Kit (que NO
    // pasan por ese pipeline de preview), ver
    // `PoseTrackerService._espejarPunto`.
    return ClipRect(
      child: FittedBox(
        fit: BoxFit.cover,
        child: preview,
      ),
    );
  }
}

class _CameraMensaje extends StatelessWidget {
  const _CameraMensaje({required this.mensaje});

  final String mensaje;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.videocam_off_outlined, size: 40, color: AppColors.cream),
          const SizedBox(height: AppSpacing.sm),
          Text(
            mensaje,
            textAlign: TextAlign.center,
            style: AppTextStyles.body.copyWith(color: AppColors.cream),
          ),
        ],
      ),
    );
  }
}
