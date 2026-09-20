import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../features/sucursales/models/sucursal.dart';

/// Card de sucursal (CU07) -- reutilizable también por CU12 (selector de
/// sucursal para consultar disponibilidad), por eso vive en `shared/widgets`
/// igual que [ProductCard]. Muestra únicamente campos reales de
/// `SucursalPublicaOut`: nombre, ciudad, dirección y teléfono -- no hay
/// horario en el contrato real, así que no se inventa uno.
///
/// Superficie crema/beige con un bloque de identidad burdeos (no la card
/// completa en rojo) e iconos rojos para dirección/teléfono.
class SucursalCard extends StatelessWidget {
  const SucursalCard({super.key, required this.sucursal, required this.onTap});

  final Sucursal sucursal;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.cream,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(color: AppColors.divider),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: AppColors.burgundy,
                borderRadius: BorderRadius.circular(AppRadius.md),
              ),
              child: const Icon(Icons.storefront_outlined, color: AppColors.cream, size: 24),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    sucursal.nombre,
                    style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w700),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    sucursal.ciudad.nombre,
                    style: AppTextStyles.eyebrow.copyWith(color: AppColors.red, fontSize: 11),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  _InfoRow(icon: Icons.place_outlined, text: sucursal.direccion),
                  const SizedBox(height: 4),
                  _InfoRow(icon: Icons.call_outlined, text: sucursal.telefono),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppColors.textSecondary),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 14, color: AppColors.red),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            text,
            style: AppTextStyles.bodyMuted,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}
