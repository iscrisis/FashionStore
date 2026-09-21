import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_radius.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/utils/media_url.dart';
import '../models/reserva.dart';
import '../reserva_formato.dart';

/// Modal de confirmación de CU19 -- Cancelar reserva (Cliente). Mismo
/// lenguaje visual que `ReservaConfirmacionDialog` (CU17): tarjeta redondeada
/// centrada sobre `AppColors.cream`, nunca el `AlertDialog` genérico de
/// Flutter -- calcado del modal de Angular (cancelar-reserva.html): resumen
/// de la prenda (imagen, nombre, código de reserva, sucursal, fecha/horario)
/// + "¿Deseas cancelar esta reserva?" + dos acciones.
///
/// El propio diálogo llama a `onConfirmar` (que ya trae el token resuelto
/// desde quien lo abre) y maneja su propio estado de carga/error -- si tiene
/// éxito, se cierra devolviendo el [ReservaDetalleOut] actualizado (estado
/// CANCELADA) para que MisReservasPage reemplace esa única prenda sin
/// recargar toda la lista. Errores nunca muestran el detalle técnico (código
/// HTTP, excepción cruda): siempre un mensaje amigable fijo, igual que pide
/// CU19.
Future<ReservaDetalleOut?> mostrarCancelarReservaDialog(
  BuildContext context, {
  required ReservaOut reserva,
  required ReservaDetalleOut detalle,
  required Future<ReservaDetalleOut> Function() onConfirmar,
}) {
  return showDialog<ReservaDetalleOut>(
    context: context,
    builder: (_) => _CancelarReservaDialog(reserva: reserva, detalle: detalle, onConfirmar: onConfirmar),
  );
}

class _CancelarReservaDialog extends StatefulWidget {
  const _CancelarReservaDialog({required this.reserva, required this.detalle, required this.onConfirmar});

  final ReservaOut reserva;
  final ReservaDetalleOut detalle;
  final Future<ReservaDetalleOut> Function() onConfirmar;

  @override
  State<_CancelarReservaDialog> createState() => _CancelarReservaDialogState();
}

class _CancelarReservaDialogState extends State<_CancelarReservaDialog> {
  bool _cancelando = false;
  String? _errorMensaje;

  Future<void> _confirmar() async {
    if (_cancelando) return;
    setState(() {
      _cancelando = true;
      _errorMensaje = null;
    });
    try {
      final actualizado = await widget.onConfirmar();
      if (!mounted) return;
      Navigator.of(context).pop(actualizado);
    } on ApiException {
      if (!mounted) return;
      setState(() {
        _cancelando = false;
        _errorMensaje = 'No se pudo cancelar esta prenda. Inténtalo nuevamente.';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cancelando = false;
        _errorMensaje = 'No se pudo cancelar esta prenda. Inténtalo nuevamente.';
      });
    }
  }

  void _volver() {
    if (_cancelando) return;
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final imagenUrl = MediaUrl.resolve(widget.detalle.producto.imagenPrincipalUrl);

    return Dialog(
      backgroundColor: AppColors.cream,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.lg)),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '¿Deseas cancelar esta reserva?',
              textAlign: TextAlign.center,
              style: AppTextStyles.sectionTitle,
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
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                    child: Container(
                      width: 52,
                      height: 52,
                      color: AppColors.cream,
                      child: imagenUrl != null
                          ? Image.network(
                              imagenUrl,
                              fit: BoxFit.cover,
                              errorBuilder: (_, _, _) => const _ImagenPlaceholder(),
                            )
                          : const _ImagenPlaceholder(),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.detalle.producto.nombre,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Reserva ${widget.reserva.codigoReserva}',
                          style: AppTextStyles.bodyMuted.copyWith(
                            color: AppColors.burgundy,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${widget.reserva.sucursal.nombre} · ${widget.reserva.sucursal.ciudad.nombre}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: AppTextStyles.bodyMuted,
                        ),
                        Text(
                          '${formatearFechaReserva(widget.reserva.fechaReserva)} · '
                          '${formatearHorarioReserva(widget.reserva.horaInicio, widget.reserva.horaFin)}',
                          style: AppTextStyles.bodyMuted,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            if (_errorMensaje != null) ...[
              const SizedBox(height: AppSpacing.md),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: BoxDecoration(
                  color: AppColors.red.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(AppRadius.md),
                  border: Border.all(color: AppColors.red.withValues(alpha: 0.25)),
                ),
                child: Text(_errorMensaje!, style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy)),
              ),
            ],
            const SizedBox(height: AppSpacing.xl),
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 46,
                    child: OutlinedButton(
                      onPressed: _cancelando ? null : _volver,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.charcoal,
                        side: const BorderSide(color: AppColors.divider),
                        padding: EdgeInsets.zero,
                      ),
                      child: const Text('Volver'),
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: SizedBox(
                    height: 46,
                    child: ElevatedButton(
                      onPressed: _cancelando ? null : _confirmar,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.red,
                        foregroundColor: AppColors.cream,
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        textStyle: AppTextStyles.button.copyWith(fontSize: 12.5, letterSpacing: 0.2),
                      ),
                      child: FittedBox(
                        fit: BoxFit.scaleDown,
                        child: Text(
                          _cancelando ? 'Cancelando...' : 'Confirmar cancelación',
                          maxLines: 1,
                          softWrap: false,
                          overflow: TextOverflow.visible,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ImagenPlaceholder extends StatelessWidget {
  const _ImagenPlaceholder();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Icon(Icons.checkroom_outlined, size: 20, color: AppColors.textSecondary),
    );
  }
}
