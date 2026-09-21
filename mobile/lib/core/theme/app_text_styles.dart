import 'package:flutter/material.dart';

import 'app_colors.dart';

/// Estilos de texto reutilizables. El look editorial se logra con peso,
/// tracking y jerarquía de tamaño sobre la tipografía por defecto de
/// Flutter (Roboto) -- no se agrega ninguna fuente externa porque no hace
/// falta para conseguirlo.
class AppTextStyles {
  AppTextStyles._();

  static const TextStyle brand = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w700,
    letterSpacing: 3,
    color: AppColors.charcoal,
  );

  static const TextStyle display = TextStyle(
    fontSize: 26,
    fontWeight: FontWeight.w300,
    letterSpacing: 0.2,
    height: 1.2,
    color: AppColors.charcoal,
  );

  static const TextStyle sectionTitle = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w600,
    color: AppColors.charcoal,
  );

  static const TextStyle eyebrow = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w600,
    letterSpacing: 2.2,
    color: AppColors.textSecondary,
  );

  static const TextStyle body = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w400,
    height: 1.4,
    color: AppColors.charcoal,
  );

  static const TextStyle bodyMuted = TextStyle(
    fontSize: 13,
    fontWeight: FontWeight.w400,
    color: AppColors.textSecondary,
  );

  static const TextStyle price = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w700,
    color: AppColors.burgundy,
  );

  static const TextStyle priceDiscount = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w700,
    color: AppColors.red,
  );

  static const TextStyle priceStrike = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w400,
    color: AppColors.textSecondary,
    decoration: TextDecoration.lineThrough,
  );

  static const TextStyle button = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.5,
  );

  static const TextStyle navLabel = TextStyle(
    fontSize: 11,
    fontWeight: FontWeight.w500,
  );
}
