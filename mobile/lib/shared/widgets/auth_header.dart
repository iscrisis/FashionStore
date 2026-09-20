import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';

/// Encabezado editorial compartido por las pantallas de autenticación
/// (CU01 Login, CU02 Registro): degradado burdeos/rojo + acento geométrico
/// dorado, sin fotografías. Un solo widget para no duplicar este bloque
/// entre pantallas -- solo cambia el texto ([eyebrow]) y si tiene sentido
/// mostrar una flecha de "volver" ([mostrarVolver]).
class AuthHeader extends StatelessWidget {
  const AuthHeader({
    super.key,
    required this.eyebrow,
    required this.mostrarVolver,
    required this.onCerrar,
  });

  final String eyebrow;
  final bool mostrarVolver;
  final VoidCallback onCerrar;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(AppSpacing.sm, AppSpacing.sm, AppSpacing.lg, AppSpacing.xl),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.burgundy, AppColors.burgundy, AppColors.red],
          stops: [0, 0.55, 1],
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            right: -30,
            top: -20,
            child: Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.gold.withValues(alpha: 0.16),
              ),
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (mostrarVolver)
                IconButton(
                  onPressed: onCerrar,
                  icon: const Icon(Icons.arrow_back, color: AppColors.cream),
                )
              else
                const SizedBox(height: AppSpacing.xl + AppSpacing.sm),
              const SizedBox(height: AppSpacing.md),
              Padding(
                padding: const EdgeInsets.only(left: AppSpacing.sm),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('FASHIONSTORE', style: AppTextStyles.brand.copyWith(color: AppColors.cream)),
                    const SizedBox(height: AppSpacing.xs),
                    Text(eyebrow, style: AppTextStyles.eyebrow.copyWith(color: AppColors.gold)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
