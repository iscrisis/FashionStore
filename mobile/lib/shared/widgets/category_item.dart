import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/media_url.dart';
import '../../features/catalogo/models/categoria.dart';

/// Card compacta de categoría para el scroll horizontal de la Home. Si la
/// categoría no tiene `imagen_url` real, se usa una presentación neutra
/// (icono genérico) -- nunca un ícono inventado por categoría.
class CategoryItem extends StatelessWidget {
  const CategoryItem({super.key, required this.categoria, required this.onTap});

  final Categoria categoria;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final imageUrl = MediaUrl.resolve(categoria.imagenUrl);

    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: SizedBox(
        width: 78,
        child: Column(
          children: [
            Container(
              width: 68,
              height: 68,
              decoration: BoxDecoration(
                color: AppColors.surface,
                shape: BoxShape.circle,
                border: Border.all(color: AppColors.burgundy.withValues(alpha: 0.12)),
              ),
              clipBehavior: Clip.antiAlias,
              child: imageUrl != null
                  ? Image.network(
                      imageUrl,
                      fit: BoxFit.cover,
                      errorBuilder: (_, _, _) => const _NeutralIcon(),
                    )
                  : const _NeutralIcon(),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              categoria.nombre,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: AppTextStyles.bodyMuted.copyWith(
                color: AppColors.charcoal,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NeutralIcon extends StatelessWidget {
  const _NeutralIcon();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Icon(Icons.checkroom_outlined, color: AppColors.burgundy, size: 24),
    );
  }
}
