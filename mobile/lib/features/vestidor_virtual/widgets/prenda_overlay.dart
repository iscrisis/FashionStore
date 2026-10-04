import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter/services.dart' show rootBundle;

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_radius.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_text_styles.dart';
import '../models/torso_pose.dart';
import '../services/pose_coordinate_transformer.dart';

/// Superpone el PNG transparente de la prenda seleccionada sobre la vista
/// de cámara.
///
/// Posición y escala salen de UNA de estas dos fuentes, nunca ambas a la
/// vez:
/// - [torso] (detección de pose EN VIVO, ver `PoseTrackerService`):
///   cuando hay una persona con hombros/caderas visibles, la prenda se
///   centra en su torso real y se escala según su ancho aproximado --
///   conservando siempre la proporción ancho:alto que ya define la
///   categoría (ver `ConfiguracionPrendaCategoria`), nunca la deforma.
/// - [alineacionInicial]/[widthFactor]/[heightFactor] (config estática
///   por categoría) cuando [torso] es `null` -- SIN persona detectada,
///   sin hombros visibles, con poca luz, o si la cámara/el detector
///   fallan por cualquier motivo. Este es el comportamiento ORIGINAL del
///   CU y sigue siendo el fallback obligatorio: la prenda NUNCA
///   desaparece ni deja la pantalla vacía por falta de detección.
///
/// [scale]/[offset] (ver `OverlayControles`) son un ajuste manual
/// ADICIONAL que el Cliente aplica siempre por encima de cualquiera de
/// las dos fuentes de arriba, nunca las reemplaza.
///
/// La representación visual depende PRINCIPALMENTE de que exista el
/// recurso virtual (`assets/vestidor/producto_<id>.png`, ver
/// `PrendaVirtual`) -- es un recurso ADICIONAL de la prenda, totalmente
/// independiente de la imagen normal del catálogo
/// (`imagenCatalogoUrl`/`Producto.imagenPrincipalUrl`, servida por el
/// backend): si el PNG todavía no está preparado, esta vista lo informa
/// de forma elegante (`_VistaNoDisponible`) en vez de mostrar un error
/// técnico o tumbar la pantalla -- la galería del catálogo sigue
/// funcionando exactamente igual en `producto_detalle_page.dart`.
class PrendaOverlay extends StatefulWidget {
  const PrendaOverlay({
    super.key,
    required this.assetPath,
    required this.alineacionInicial,
    required this.widthFactor,
    required this.heightFactor,
    this.torso,
    this.scale = 1,
    this.offset = Offset.zero,
    this.opacidad = 0.92,
    this.factorAnchoPrenda = 2.83,
    this.onDisponibilidadResuelta,
  });

  final String assetPath;

  /// Punto/tamaño del encuadre donde nace la prenda cuando NO hay
  /// detección de torso (ver `configuracionParaCategoria`) --
  /// `Transform.translate`/[offset] mueve DESDE ahí, nunca reemplaza
  /// esta posición base. También aporta la proporción ancho:alto que se
  /// conserva cuando SÍ hay [torso].
  final Alignment alineacionInicial;
  final double widthFactor;
  final double heightFactor;

  /// Torso detectado en el frame más reciente (ver `PoseTrackerService`
  /// / `CameraView`). `null` = sin detección utilizable ahora mismo
  /// (nadie frente a la cámara, poca luz, detector no disponible) --
  /// en ese caso se usa [alineacionInicial]/[widthFactor]/[heightFactor].
  final TorsoPose? torso;

  final double scale;
  final Offset offset;

  /// Ligeramente por debajo de 1 a propósito -- ayuda a que la prenda se
  /// perciba integrada con el video de la cámara en vez de un sticker
  /// pegado encima. Configurable (no fijo) por si una prenda concreta
  /// necesita más o menos integración.
  final double opacidad;

  /// Cuánto más ancha se dibuja la prenda que la distancia hombro-a-
  /// hombro real detectada (drape + mangas) -- multiplicador visual,
  /// NUNCA una medida corporal. `2.83` por defecto -- calibrado en vivo
  /// contra el cuerpo real (el valor original, `2.0`, quedaba angosto:
  /// no llegaba a cubrir hombros/brazos).
  final double factorAnchoPrenda;

  /// Notifica hacia arriba si el PNG existe o no, para que la pantalla
  /// pueda deshabilitar `OverlayControles` cuando no hay nada que mover.
  final ValueChanged<bool>? onDisponibilidadResuelta;

  @override
  State<PrendaOverlay> createState() => _PrendaOverlayState();
}

class _PrendaOverlayState extends State<PrendaOverlay> with SingleTickerProviderStateMixin {
  // null mientras se resuelve -- evita el parpadeo de mostrar
  // "no disponible" por una fracción de segundo antes de confirmar que sí
  // existe el asset.
  bool? _disponible;

  // Animación de "aparición" (fade + escala con leve rebote) para que la
  // prenda se sienta materializada sobre la cámara en vez de aparecer de
  // golpe como un sticker pegado. Se reproduce cada vez que el PNG
  // resuelto pasa a estar disponible.
  late final AnimationController _entrada = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 420),
  );
  late final Animation<double> _escalaEntrada = CurvedAnimation(parent: _entrada, curve: Curves.easeOutBack);

  @override
  void initState() {
    super.initState();
    _verificarDisponibilidad();
  }

  @override
  void didUpdateWidget(covariant PrendaOverlay oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.assetPath != widget.assetPath) {
      setState(() => _disponible = null);
      _verificarDisponibilidad();
    }
  }

  @override
  void dispose() {
    _entrada.dispose();
    super.dispose();
  }

  /// Confirma con `rootBundle` si el PNG de este producto/vista ya está
  /// en `assets/vestidor/` ANTES de intentar dibujarlo -- así se evita
  /// cualquier excepción de decodificación de imagen visible para el
  /// Cliente (nada de "errores técnicos" en pantalla).
  Future<void> _verificarDisponibilidad() async {
    bool disponible;
    try {
      await rootBundle.load(widget.assetPath);
      disponible = true;
    } catch (_) {
      disponible = false;
    }
    if (!mounted) return;
    _aplicarDisponibilidad(disponible);
  }

  /// Si `rootBundle.load` resuelve tan rápido que su continuación cae
  /// DENTRO de la misma pasada de construcción del widget padre (posible
  /// cuando el asset ya está en caché), llamar `setState` acá mismo
  /// dispara "setState() called during build". Se difiere al final del
  /// frame en curso con `addPostFrameCallback`; si no hay ningún frame en
  /// construcción (caso normal: la app está en reposo esperando el
  /// resultado de disco), se aplica de inmediato.
  void _aplicarDisponibilidad(bool disponible) {
    void aplicar() {
      if (!mounted) return;
      setState(() => _disponible = disponible);
      widget.onDisponibilidadResuelta?.call(disponible);
      if (disponible) {
        _entrada.forward(from: 0);
      } else {
        _entrada.value = 0;
      }
    }

    if (SchedulerBinding.instance.schedulerPhase == SchedulerPhase.persistentCallbacks) {
      SchedulerBinding.instance.addPostFrameCallback((_) => aplicar());
    } else {
      aplicar();
    }
  }

  @override
  Widget build(BuildContext context) {
    final disponible = _disponible;
    if (disponible == null) return const SizedBox.shrink();
    if (!disponible) return const _VistaNoDisponible();

    final torso = widget.torso;
    // `LayoutBuilder` es OBLIGATORIO para la rama con torso: el tamaño
    // real del widget es justo lo que `transformPosePointToScreen`
    // necesita para convertir el punto del FRAME (que puede estar
    // recortado por el `BoxFit.cover` de `CameraView`) a una posición
    // real en pantalla -- nunca se asume ni se calcula "a ojo".
    return LayoutBuilder(
      builder: (context, constraints) {
        if (torso != null) {
          return _prendaSobreTorso(torso, constraints.biggest);
        }
        // Fallback obligatorio -- ver docstring de la clase.
        return _prendaEnPosicionEstatica();
      },
    );
  }

  /// Rama SIN detección de torso -- posición/tamaño de la config de
  /// categoría, expresados como fracción del widget (no necesitan la
  /// transformación de `transformPosePointToScreen` porque no vienen de
  /// un frame de cámara).
  Widget _prendaEnPosicionEstatica() {
    return Align(
      alignment: widget.alineacionInicial,
      child: Transform.translate(
        offset: widget.offset,
        child: Transform.scale(
          scale: widget.scale,
          child: FractionallySizedBox(
            widthFactor: widget.widthFactor,
            heightFactor: widget.heightFactor,
            child: _contenidoPrenda(),
          ),
        ),
      ),
    );
  }

  /// Rama CON torso detectado -- convierte el centro y el ancho de
  /// hombros (en píxeles del frame, ver `TorsoPose`) a píxeles REALES
  /// de pantalla con la ÚNICA función de transformación del módulo, y
  /// posiciona la prenda con coordenadas absolutas (`Align.topLeft` +
  /// `Transform.translate`, NO `Positioned`: este widget vive dentro de
  /// un `IgnorePointer` en el `Stack` de `VestidorVirtualPage`, y
  /// `Positioned` exige ser hijo DIRECTO de un `Stack` en el árbol de
  /// render -- `Align`/`Transform.translate` no tienen esa restricción
  /// y logran el mismo posicionamiento absoluto). Nunca se usa
  /// `Alignment` proporcional aquí -- esa era la cuenta que asumía "la
  /// mitad del frame" = "la mitad del widget", el supuesto que rompía
  /// el posicionamiento cuando la cámara y la pantalla no comparten
  /// proporción.
  Widget _prendaSobreTorso(TorsoPose torso, Size tamanoWidget) {
    final centroPantalla = transformPosePointToScreen(
      puntoFrame: torso.centro,
      tamanoFrame: torso.tamanoFrame,
      tamanoWidget: tamanoWidget,
    );
    final anchoHombrosPantalla = transformPoseDistanceToScreen(
      distanciaFrame: torso.anchoHombros,
      tamanoFrame: torso.tamanoFrame,
      tamanoWidget: tamanoWidget,
    );

    // Conserva la proporción ancho:alto que ya definía la categoría
    // (nunca deforma la prenda), ahora aplicada sobre un ancho en
    // píxeles reales de pantalla en vez de una fracción del frame.
    final ratioAltoAncho = widget.widthFactor > 0 ? widget.heightFactor / widget.widthFactor : 1.0;
    // El techo de 0.92 (antes) cortaba el ancho ANTES de que
    // `factorAnchoPrenda` pudiera surtir efecto: la distancia
    // hombro-a-hombro real en píxeles de pantalla es angosta (es la
    // medida ósea, el punto más angosto del torso) -- multiplicada por
    // un factor generoso para cubrir brazos/mangas fácilmente supera el
    // 92% del ancho del widget, así que CUALQUIER factor por encima de
    // ~2.3 quedaba pisado por este techo sin ningún efecto visible.
    // Confirmado en dispositivo: subir el slider hasta el máximo (4.0)
    // no cambiaba nada a partir de cierto punto.
    final anchoPrenda = (anchoHombrosPantalla * widget.factorAnchoPrenda).clamp(
      tamanoWidget.width * 0.22,
      tamanoWidget.width * 1.15,
    );
    final altoPrenda = (anchoPrenda * ratioAltoAncho).clamp(tamanoWidget.height * 0.18, tamanoWidget.height * 0.95);

    final left = centroPantalla.dx - anchoPrenda / 2 + widget.offset.dx;
    final top = centroPantalla.dy - altoPrenda / 2 + widget.offset.dy;

    return Align(
      alignment: Alignment.topLeft,
      child: Transform.translate(
        offset: Offset(left, top),
        child: SizedBox(
          width: anchoPrenda,
          height: altoPrenda,
          child: Transform.scale(scale: widget.scale, child: _contenidoPrenda()),
        ),
      ),
    );
  }

  Widget _contenidoPrenda() {
    return FadeTransition(
      opacity: _entrada,
      child: ScaleTransition(
        scale: _escalaEntrada,
        child: Stack(
          alignment: Alignment.bottomCenter,
          clipBehavior: Clip.none,
          children: [
            // Sombra suave debajo de la prenda -- un óvalo oscuro
            // desenfocado (sin librerías externas, solo
            // `ImageFilter.blur` propio de Flutter) para dar sensación
            // de profundidad/apoyo sobre el cuerpo, en vez de una
            // prenda "flotando" plana sobre el video.
            Positioned(
              bottom: -6,
              child: ImageFiltered(
                imageFilter: ImageFilter.blur(sigmaX: 12, sigmaY: 7),
                child: Container(
                  width: 90,
                  height: 18,
                  decoration: BoxDecoration(
                    color: Colors.black.withValues(alpha: 0.32),
                    borderRadius: BorderRadius.circular(40),
                  ),
                ),
              ),
            ),
            // `filterQuality: high` suaviza los bordes del recorte al
            // escalar (bordes suaves sin procesar la imagen con
            // librerías externas); `BoxFit.contain` es lo que
            // realmente evita deformar la prenda.
            Opacity(
              opacity: widget.opacidad,
              child: Image.asset(widget.assetPath, fit: BoxFit.contain, filterQuality: FilterQuality.high),
            ),
          ],
        ),
      ),
    );
  }
}

class _VistaNoDisponible extends StatelessWidget {
  const _VistaNoDisponible();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        margin: const EdgeInsets.all(AppSpacing.xl),
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg, vertical: AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.cream.withValues(alpha: 0.94),
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(color: AppColors.burgundy.withValues(alpha: 0.4)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.checkroom_outlined, size: 40, color: AppColors.burgundy),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Vista virtual no disponible para esta prenda',
              textAlign: TextAlign.center,
              style: AppTextStyles.body.copyWith(color: AppColors.charcoal, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }
}
