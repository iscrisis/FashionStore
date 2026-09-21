import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/media_url.dart';
import '../../features/catalogo/models/producto.dart';

/// Card de producto reutilizable (Home y catálogo completo). Solo muestra
/// datos reales del backend: imagen (si existe), nombre y precio. El precio
/// de promoción usa directamente `precio_base`/`precio_final`/
/// `en_promocion`/`porcentaje_descuento` que ya calcula FastAPI (CU32) --
/// nunca se recalcula aquí.
class ProductCard extends StatelessWidget {
  const ProductCard({super.key, required this.producto, required this.onTap});

  final Producto producto;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final imageUrl = MediaUrl.resolve(producto.imagenPrincipalUrl);

    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(AppRadius.md),
              child: Container(
                color: AppColors.surface,
                width: double.infinity,
                child: imageUrl != null
                    ? Image.network(
                        imageUrl,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => const _ProductPlaceholder(),
                      )
                    : const _ProductPlaceholder(),
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            producto.nombre,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w500),
          ),
          const SizedBox(height: 2),
          Wrap(
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: AppSpacing.xs,
            children: [
              Text(
                'Bs ${producto.precioFinal.toStringAsFixed(2)}',
                style: producto.enPromocion ? AppTextStyles.priceDiscount : AppTextStyles.price,
              ),
              if (producto.enPromocion)
                Text('Bs ${producto.precioBase.toStringAsFixed(2)}', style: AppTextStyles.priceStrike),
            ],
          ),
        ],
      ),
    );
  }
}

class _ProductPlaceholder extends StatelessWidget {
  const _ProductPlaceholder();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Icon(Icons.checkroom_outlined, size: 32, color: AppColors.textSecondary),
    );
  }
}
