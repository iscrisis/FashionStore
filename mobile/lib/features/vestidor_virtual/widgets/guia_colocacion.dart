import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_radius.dart';
import '../../../core/theme/app_text_styles.dart';

/// Guía visual ESTÁTICA de encuadre -- un simple marco de referencia +
/// una indicación de texto para que el Cliente se ubique frente a la
/// cámara. Es un dibujo fijo, siempre igual, que NO analiza el video por
/// sí mismo: la detección de pose real ocurre aparte, en
/// `PoseTrackerService`/`CameraView` -- este widget solo sugiere DÓNDE
/// pararse, sin afirmar ni depender de que la detección sea perfecta.
/// Vive DEBAJO de `PrendaOverlay` en el `Stack` de
/// `VestidorVirtualPage` (mismo orden que un vestidor real: primero te
/// ubicás en el marco, después se ve la prenda encima), sobre la cámara
/// a pantalla completa.
class GuiaColocacion extends StatelessWidget {
  const GuiaColocacion({super.key});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Align(
          alignment: const Alignment(0, -0.58),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.charcoal.withValues(alpha: 0.55),
              borderRadius: BorderRadius.circular(AppRadius.pill),
            ),
            child: Text(
              'Colócate frente a la cámara',
              textAlign: TextAlign.center,
              style: AppTextStyles.bodyMuted.copyWith(
                color: AppColors.cream,
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ),
        Align(
          alignment: const Alignment(0, -0.02),
          child: FractionallySizedBox(
            widthFactor: 0.62,
            heightFactor: 0.62,
            child: DecoratedBox(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(AppRadius.lg),
                border: Border.all(color: AppColors.cream.withValues(alpha: 0.32), width: 1.4),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
