import 'package:flutter/material.dart';

/// Variante visual del [PrimaryButton] -- `filled` para uso normal sobre
/// fondo crema, `outline` para uso sobre paneles oscuros (hero editorial).
enum PrimaryButtonVariant { filled, outline }

/// Botón de acción reutilizable. Envuelve `ElevatedButton`/`OutlinedButton`
/// del tema global -- ninguna pantalla debe definir su propio estilo de
/// botón principal.
class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.variant = PrimaryButtonVariant.filled,
    this.expand = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final PrimaryButtonVariant variant;
  final bool expand;

  @override
  Widget build(BuildContext context) {
    final Widget button = variant == PrimaryButtonVariant.outline
        ? OutlinedButton(onPressed: onPressed, child: Text(label))
        : ElevatedButton(onPressed: onPressed, child: Text(label));

    return expand ? SizedBox(width: double.infinity, child: button) : button;
  }
}
