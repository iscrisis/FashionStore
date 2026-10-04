import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import 'models/configuracion_prenda_categoria.dart';
import 'models/prenda_virtual.dart';
import 'models/torso_pose.dart';
import 'widgets/camera_view.dart';
import 'widgets/guia_colocacion.dart';
import 'widgets/overlay_controles.dart';
import 'widgets/prenda_overlay.dart';

/// Último caso de uso: "Utilizar vestidor virtual mediante cámara móvil".
/// Se abre desde `ProductoDetallePage` al presionar "Probar virtualmente",
/// ya con talla/color elegidos. Cámara en vivo (en modo espejo, ver
/// `CameraView`) + overlay 2D de la prenda cuya posición/escala se ajusta
/// con detección básica de pose (ML Kit Pose Detection, ver
/// `PoseTrackerService`) -- SIN reconocimiento de identidad, análisis
/// corporal, mediciones, recomendaciones de talla, IA generativa, avatar
/// 3D ni motores de AR externos (ARCore/ARKit).
///
/// La CÁMARA es el fondo de TODA la pantalla (`Stack` a pantalla completa,
/// sin ninguna tarjeta oscura que la encierre) -- encabezado, controles y
/// nota inferior son overlays flotantes y traslúcidos sobre el video,
/// como una app de cámara comercial, nunca un bloque separado que le
/// robe espacio al preview.
///
/// Es `StatefulWidget` para sostener tamaño/posición del overlay
/// (`_escala`/`_desplazamiento`, ajuste manual ADICIONAL, ver
/// `OverlayControles`), el último torso detectado (`_torso`, ver
/// `TorsoPose`) y si el PNG correspondiente existe (`_overlayDisponible`)
/// -- nada de esto depende de red ni de sesión, vive y muere con esta
/// pantalla.
class VestidorVirtualPage extends StatefulWidget {
  const VestidorVirtualPage({super.key, required this.prenda});

  final PrendaVirtual prenda;

  @override
  State<VestidorVirtualPage> createState() => _VestidorVirtualPageState();
}

class _VestidorVirtualPageState extends State<VestidorVirtualPage> {
  static const double _escalaMin = 0.6;
  static const double _escalaMax = 1.8;
  static const double _escalaPaso = 0.1;
  static const double _desplazamientoPaso = 14;
  static const double _desplazamientoLimite = 90;

  // La prenda nace en la posición/escala "inteligente" de su categoría
  // (offset cero, escala 1 sobre `ConfiguracionPrendaCategoria` -- ver
  // `_configuracion` abajo); el Cliente ajusta desde ahí con
  // `OverlayControles`, como un adicional por encima de lo que ya se
  // haya detectado (o no) del torso.
  double _escala = 1;
  Offset _desplazamiento = Offset.zero;

  // Último torso detectado por `CameraView`/`PoseTrackerService`. `null`
  // = sin detección utilizable todavía (nadie frente a la cámara, poca
  // luz, detector no disponible) -- en ese caso `PrendaOverlay` cae SOLA
  // a `_configuracion` (posición/escala manual existente, el
  // comportamiento ORIGINAL del CU). A propósito NUNCA se pisa con
  // `null` cuando un frame puntual no detecta nada: solo se actualiza
  // con una detección nueva, para no hacer parpadear la prenda entre
  // "trackeada" y "fallback" por un solo frame perdido.
  TorsoPose? _torso;

  // null mientras `PrendaOverlay` todavía no confirma si el PNG existe;
  // los controles quedan deshabilitados hasta que hay algo que mover.
  bool? _overlayDisponible;

  /// Configuración estática por categoría (Blusas, Vestidos, Pantalones,
  /// ...) -- ver `configuracionParaCategoria`. Se calcula una sola vez:
  /// la categoría del producto no cambia dentro de esta pantalla. Sirve
  /// de fallback Y de referencia de proporción (ancho:alto) cuando SÍ
  /// hay torso detectado (ver `PrendaOverlay`).
  late final ConfiguracionPrendaCategoria _configuracion = configuracionParaCategoria(
    widget.prenda.categoriaNombre,
  );

  @override
  void initState() {
    super.initState();
    // Bloquea la orientación a portrait mientras se usa la cámara del
    // vestidor -- CAUSA RAÍZ auditada del bug de landmarks rotados/
    // desplazados: sin este bloqueo, `camera_android_camerax` puede
    // reportar `CameraController.value.deviceOrientation` de forma
    // inestable durante el arranque del stream (todavía no hay una
    // orientación de UI "asentada" para leer), lo que sumaba un offset
    // de 90°/270° incorrecto a la rotación real del sensor
    // (`PoseTrackerService._rotacionDe`). Probar una prenda sosteniendo
    // el teléfono en horizontal no tiene sentido de todos modos, así que
    // fijar portrait acá no le quita nada al CU. Se restaura al salir
    // (ver `dispose`) para no afectar al resto de la app.
    unawaited(SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]));
  }

  @override
  void dispose() {
    unawaited(SystemChrome.setPreferredOrientations(DeviceOrientation.values));
    super.dispose();
  }

  void _onTorsoDetectado(TorsoPose? torso) {
    if (torso == null || !mounted) return;
    setState(() => _torso = torso);
  }

  void _aumentar() {
    setState(() => _escala = (_escala + _escalaPaso).clamp(_escalaMin, _escalaMax));
  }

  void _disminuir() {
    setState(() => _escala = (_escala - _escalaPaso).clamp(_escalaMin, _escalaMax));
  }

  void _mover(Offset direccion) {
    setState(() {
      final dx = (_desplazamiento.dx + direccion.dx * _desplazamientoPaso).clamp(
        -_desplazamientoLimite,
        _desplazamientoLimite,
      );
      final dy = (_desplazamiento.dy + direccion.dy * _desplazamientoPaso).clamp(
        -_desplazamientoLimite,
        _desplazamientoLimite,
      );
      _desplazamiento = Offset(dx, dy);
    });
  }

  @override
  Widget build(BuildContext context) {
    final prenda = widget.prenda;

    return Scaffold(
      appBar: AppBar(title: const Text('Vestidor virtual')),
      // La cámara ocupa TODO el body, borde a borde -- el resto de la
      // interfaz (encabezado, controles, nota) son overlays flotantes
      // dentro del mismo Stack, nunca un contenedor separado que le
      // reste alto al preview.
      body: Stack(
        fit: StackFit.expand,
        children: [
          CameraView(onTorsoDetectado: _onTorsoDetectado),
          const IgnorePointer(child: GuiaColocacion()),
          IgnorePointer(
            child: PrendaOverlay(
              assetPath: prenda.overlayAssetPath,
              alineacionInicial: _configuracion.alineacion,
              widthFactor: _configuracion.widthFactor,
              heightFactor: _configuracion.heightFactor,
              torso: _torso,
              scale: _escala,
              offset: _desplazamiento,
              onDisponibilidadResuelta: (disponible) {
                if (!mounted) return;
                setState(() => _overlayDisponible = disponible);
              },
            ),
          ),
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: SafeArea(
              bottom: false,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(AppSpacing.md, AppSpacing.sm, AppSpacing.md, 0),
                child: _EncabezadoFlotante(prenda: prenda),
              ),
            ),
          ),
          Positioned(
            right: AppSpacing.sm,
            top: 0,
            bottom: 0,
            child: Center(
              // `FittedBox` reescala el panel completo si el alto
              // disponible es chico (pantallas bajas) en vez de
              // desbordar (overflow) o recortar botones.
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: OverlayControles(
                  habilitado: _overlayDisponible == true,
                  onAumentar: _aumentar,
                  onDisminuir: _disminuir,
                  onMover: _mover,
                ),
              ),
            ),
          ),
          const Positioned(left: 0, right: 0, bottom: 0, child: _BarraInferior()),
        ],
      ),
    );
  }
}

/// Encabezado flotante y compacto: miniatura de la imagen NORMAL del
/// catálogo (nunca el PNG del overlay -- son recursos independientes,
/// ver `PrendaVirtual`), nombre y categoría, con talla/color como chips
/// pequeños de información SECUNDARIA. Vive sobre la cámara (por eso
/// tiene su propio fondo traslúcido, a diferencia de cuando vivía en un
/// bloque aparte encima del preview) -- la prioridad visual de la
/// pantalla sigue siendo la cámara, no esta tarjeta.
class _EncabezadoFlotante extends StatelessWidget {
  const _EncabezadoFlotante({required this.prenda});

  final PrendaVirtual prenda;

  @override
  Widget build(BuildContext context) {
    final imagenUrl = prenda.imagenCatalogoUrl;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: AppSpacing.sm),
      decoration: BoxDecoration(
        color: AppColors.cream.withValues(alpha: 0.92),
        borderRadius: BorderRadius.circular(AppRadius.md),
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.16), blurRadius: 8, offset: const Offset(0, 2)),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(AppRadius.sm),
            child: Container(
              width: 40,
              height: 40,
              color: AppColors.surface,
              child: imagenUrl != null
                  ? Image.network(
                      imagenUrl,
                      fit: BoxFit.cover,
                      errorBuilder: (_, _, _) =>
                          const Icon(Icons.checkroom_outlined, size: 18, color: AppColors.textSecondary),
                    )
                  : const Icon(Icons.checkroom_outlined, size: 18, color: AppColors.textSecondary),
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  prenda.nombre,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppTextStyles.sectionTitle.copyWith(fontSize: 15),
                ),
                Text(
                  prenda.categoriaNombre,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppTextStyles.bodyMuted.copyWith(fontSize: 11.5),
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          _ChipInfo(valor: prenda.tallaNombre),
          const SizedBox(width: 6),
          _ChipInfo(valor: prenda.colorNombre),
        ],
      ),
    );
  }
}

class _ChipInfo extends StatelessWidget {
  const _ChipInfo({required this.valor});

  final String valor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.pill),
        border: Border.all(color: AppColors.divider),
      ),
      child: Text(
        valor,
        style: AppTextStyles.bodyMuted.copyWith(fontWeight: FontWeight.w600, fontSize: 11.5),
      ),
    );
  }
}

/// Franja inferior flotante -- degradado oscuro (sin recortes duros)
/// para que la nota y el botón de volver se lean bien sobre CUALQUIER
/// fondo de cámara, sin taparla con un bloque sólido.
class _BarraInferior extends StatelessWidget {
  const _BarraInferior();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.xl, AppSpacing.lg, 0),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Colors.transparent, AppColors.charcoal.withValues(alpha: 0.8)],
        ),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Esta es una vista de referencia. Ajusta la posición según tu postura.',
              textAlign: TextAlign.center,
              style: AppTextStyles.bodyMuted.copyWith(
                color: AppColors.cream,
                fontStyle: FontStyle.italic,
                fontSize: 11.5,
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () => Navigator.of(context).pop(),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.cream,
                  side: const BorderSide(color: AppColors.cream),
                ),
                icon: const Icon(Icons.arrow_back, size: 18),
                label: const Text('VOLVER AL PRODUCTO'),
              ),
            ),
            const SizedBox(height: AppSpacing.md),
          ],
        ),
      ),
    );
  }
}
