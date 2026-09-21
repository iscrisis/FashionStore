import 'package:flutter/material.dart';

/// Paleta central de FashionStore Mobile. Ningún widget debe escribir un
/// Color hexadecimal propio -- todos reutilizan estas constantes para que
/// la app se sienta visualmente consistente y un cambio de marca se haga
/// en un solo lugar.
class AppColors {
  AppColors._();

  // ~45% -- fondo cálido y superficies (beige rosado suave), no blanco puro.
  static const Color cream = Color(0xFFF1E8E1);
  static const Color surface = Color(0xFFE8D5D3);
  static const Color divider = Color(0xFFD9C1BC);

  // ~20% -- carbón/texto fuerte y navegación.
  static const Color charcoal = Color(0xFF211E1C);
  static const Color textSecondary = Color(0xFF7A6B65);

  // ~25% -- rojo FashionStore + burdeos, identidad principal/CTA.
  static const Color red = Color(0xFFA91D2A);
  static const Color burgundy = Color(0xFF6F1D2A);

  // ~10% -- dorado/mostaza, acento pequeño, nunca fondo dominante.
  static const Color gold = Color(0xFFD4A94F);

  static const Color onDark = Color(0xFFF1E8E1);
}
