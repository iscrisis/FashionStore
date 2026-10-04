import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_radius.dart';

/// Panel flotante de ajuste manual del overlay del vestidor virtual --
/// zoom y posición, con la iconografía (lupa +/-, flechas) y el look
/// "pill" flotante de una app de cámara comercial. Vive ANCLADO al borde
/// derecho de la cámara (ver `VestidorVirtualPage`), no como una barra
/// ancha debajo del preview: la prioridad de la pantalla es la cámara,
/// no los controles.
///
/// Simple y a propósito discreto: el MVP no hace ningún ajuste
/// automático (sin seguimiento corporal), así que es el propio Cliente
/// quien acomoda la prenda con estos botones. Se deshabilitan (no se
/// ocultan) cuando no hay imagen virtual que mover, para que el panel no
/// aparezca/desaparezca sobre la cámara.
class OverlayControles extends StatelessWidget {
  const OverlayControles({
    super.key,
    required this.habilitado,
    required this.onAumentar,
    required this.onDisminuir,
    required this.onMover,
  });

  final bool habilitado;
  final VoidCallback onAumentar;
  final VoidCallback onDisminuir;
  final ValueChanged<Offset> onMover;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 6),
      decoration: BoxDecoration(
        color: AppColors.cream.withValues(alpha: 0.9),
        borderRadius: BorderRadius.circular(AppRadius.pill),
        border: Border.all(color: AppColors.burgundy.withValues(alpha: 0.25)),
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.18), blurRadius: 10, offset: const Offset(0, 3)),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _BotonControl(icon: Icons.zoom_in, onTap: habilitado ? onAumentar : null),
          const SizedBox(height: 6),
          _BotonControl(icon: Icons.zoom_out, onTap: habilitado ? onDisminuir : null),
          const SizedBox(height: 14),
          _BotonControl(
            icon: Icons.keyboard_arrow_up,
            onTap: habilitado ? () => onMover(const Offset(0, -1)) : null,
          ),
          const SizedBox(height: 6),
          _BotonControl(
            icon: Icons.keyboard_arrow_down,
            onTap: habilitado ? () => onMover(const Offset(0, 1)) : null,
          ),
          const SizedBox(height: 6),
          _BotonControl(
            icon: Icons.keyboard_arrow_left,
            onTap: habilitado ? () => onMover(const Offset(-1, 0)) : null,
          ),
          const SizedBox(height: 6),
          _BotonControl(
            icon: Icons.keyboard_arrow_right,
            onTap: habilitado ? () => onMover(const Offset(1, 0)) : null,
          ),
        ],
      ),
    );
  }
}

class _BotonControl extends StatelessWidget {
  const _BotonControl({required this.icon, required this.onTap});

  final IconData icon;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final activo = onTap != null;
    return Material(
      color: activo ? AppColors.burgundy : AppColors.divider,
      shape: const CircleBorder(),
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: Icon(icon, size: 18, color: activo ? AppColors.cream : AppColors.textSecondary),
        ),
      ),
    );
  }
}
