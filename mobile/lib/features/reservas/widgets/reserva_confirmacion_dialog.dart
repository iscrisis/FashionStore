import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_radius.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_text_styles.dart';
import '../models/reserva.dart';
import '../reserva_formato.dart';

/// Confirmación de CU17 tras un `POST /reservas` exitoso -- muestra
/// ÚNICAMENTE datos reales devueltos por el backend (producto, sucursal,
/// estado, fecha/horario, código de reserva): nada inventado (ni número de
/// reserva propio, ni beneficios, ni mensajes comerciales).
class ReservaConfirmacionDialog extends StatelessWidget {
  const ReservaConfirmacionDialog({super.key, required this.reserva});

  final ReservaOut reserva;

  @override
  Widget build(BuildContext context) {
    final detalle = reserva.detalles.isNotEmpty ? reserva.detalles.first : null;

    return Dialog(
      backgroundColor: AppColors.cream,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.lg)),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 56,
              height: 56,
              alignment: Alignment.center,
              decoration: const BoxDecoration(color: AppColors.burgundy, shape: BoxShape.circle),
              child: const Icon(Icons.check, color: AppColors.cream, size: 28),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              'Reserva realizada correctamente',
              textAlign: TextAlign.center,
              style: AppTextStyles.sectionTitle,
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(
              'Código ${reserva.codigoReserva}',
              style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: AppSpacing.lg),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(AppRadius.md),
                border: Border.all(color: AppColors.divider),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (detalle != null) ...[
                    _Fila(icono: Icons.checkroom_outlined, texto: detalle.producto.nombre),
                    const SizedBox(height: AppSpacing.sm),
                  ],
                  _Fila(
                    icono: Icons.storefront_outlined,
                    texto: '${reserva.sucursal.nombre} · ${reserva.sucursal.ciudad.nombre}',
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  _Fila(
                    icono: Icons.event_outlined,
                    texto:
                        '${formatearFechaReserva(reserva.fechaReserva)} · '
                        '${formatearHorarioReserva(reserva.horaInicio, reserva.horaFin)}',
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  _Fila(icono: Icons.info_outline, texto: reserva.estadoGeneral.etiqueta),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xl),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Listo'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Fila extends StatelessWidget {
  const _Fila({required this.icono, required this.texto});

  final IconData icono;
  final String texto;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icono, size: 16, color: AppColors.burgundy),
        const SizedBox(width: AppSpacing.sm),
        Expanded(child: Text(texto, style: AppTextStyles.body)),
      ],
    );
  }
}
