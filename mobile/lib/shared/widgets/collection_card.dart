import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../features/catalogo/models/coleccion.dart';

/// Card editorial de colección (CU10/CU11) -- sin fotografías: identidad
/// FashionStore lograda con color sólido burdeos + un acento geométrico
/// dorado. Solo muestra datos reales: nombre de la colección y su temporada
/// (ambos siempre presentes en `ColeccionOut`, nunca inventados).
///
/// Se dimensiona por el padre (SizedBox en el scroll horizontal de Home,
/// celda de GridView en "Ver todas") -- por eso ocupa todo el espacio
/// disponible en vez de fijar su propio tamaño.
class CollectionCard extends StatelessWidget {
  const CollectionCard({super.key, required this.coleccion, required this.onTap});

  final Coleccion coleccion;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        width: double.infinity,
        height: double.infinity,
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.burgundy,
          borderRadius: BorderRadius.circular(AppRadius.lg),
        ),
        clipBehavior: Clip.antiAlias,
        child: Stack(
          children: [
            Positioned(
              right: -22,
              bottom: -22,
              child: Container(
                width: 84,
                height: 84,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.gold.withValues(alpha: 0.18),
                ),
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.end,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  coleccion.temporada.nombre.toUpperCase(),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppTextStyles.eyebrow.copyWith(
                    color: AppColors.gold,
                    fontSize: 10,
                    letterSpacing: 1.4,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  coleccion.nombre,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: AppTextStyles.sectionTitle.copyWith(color: AppColors.cream, fontSize: 16),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
