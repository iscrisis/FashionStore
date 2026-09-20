import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import 'models/sucursal.dart';

/// Detalle de una sucursal ya cargada por CU07 -- reutiliza el objeto en
/// memoria, sin golpear un endpoint nuevo. Sin mapa (no hay coordenadas en
/// el contrato real) y sin ningún dato inventado (horario, distancia, etc.).
///
/// `sucursal.id` queda disponible aquí mismo para cuando CU12 (disponibilidad
/// por sucursal) necesite identificarla -- esta pantalla no calcula stock,
/// solo presenta la información pública de CU07.
class SucursalDetallePage extends StatelessWidget {
  const SucursalDetallePage({super.key, required this.sucursal});

  final Sucursal sucursal;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(sucursal.nombre)),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(AppSpacing.lg),
                decoration: BoxDecoration(
                  color: AppColors.burgundy,
                  borderRadius: BorderRadius.circular(AppRadius.lg),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: AppColors.cream.withValues(alpha: 0.14),
                        borderRadius: BorderRadius.circular(AppRadius.md),
                      ),
                      child: const Icon(Icons.storefront_outlined, color: AppColors.cream, size: 26),
                    ),
                    const SizedBox(height: AppSpacing.md),
                    Text(
                      sucursal.ciudad.nombre.toUpperCase(),
                      style: AppTextStyles.eyebrow.copyWith(color: AppColors.gold),
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      sucursal.nombre,
                      style: AppTextStyles.display.copyWith(color: AppColors.cream, fontSize: 22),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.lg),
              _DatoRow(icon: Icons.place_outlined, label: 'Dirección', valor: sucursal.direccion),
              const SizedBox(height: AppSpacing.md),
              _DatoRow(icon: Icons.call_outlined, label: 'Teléfono', valor: sucursal.telefono),
            ],
          ),
        ),
      ),
    );
  }
}

class _DatoRow extends StatelessWidget {
  const _DatoRow({required this.icon, required this.label, required this.valor});

  final IconData icon;
  final String label;
  final String valor;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 40,
          height: 40,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(AppRadius.md),
          ),
          child: Icon(icon, size: 18, color: AppColors.red),
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: AppTextStyles.eyebrow.copyWith(fontSize: 10)),
              const SizedBox(height: 2),
              Text(valor, style: AppTextStyles.body),
            ],
          ),
        ),
      ],
    );
  }
}
