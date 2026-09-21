import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_radius.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_text_styles.dart';
import '../crear_reserva_service.dart';
import '../horario_reserva.dart';
import '../models/reserva.dart';

/// Hoja "Programar reserva" de CU17 -- se abre desde el detalle de producto
/// una vez hay producto+variante+sucursal elegidos (ver producto_detalle_page.dart).
/// Solo pide fecha y horario (bloques de 1h, mismas reglas que
/// horario_reserva.dart) porque son los ÚNICOS datos que todavía faltan --
/// producto, variante, talla/color y sucursal ya vienen resueltos desde la
/// ficha y se muestran arriba, para que el Cliente sienta que está
/// reservando ESA prenda puntual, no llenando un formulario genérico.
///
/// Al confirmar, llama al POST /reservas real y devuelve la [ReservaOut] al
/// cerrar (`Navigator.pop(reserva)`) -- quien abrió la hoja decide qué
/// mostrar después (ver _mostrarConfirmacion en producto_detalle_page.dart;
/// la tarjeta de confirmación en sí NO se toca acá). La validación real de
/// fecha/horario/disponibilidad ocurre SIEMPRE en el backend (ver CU17
/// service.py); esta hoja solo arma la interfaz con las mismas reglas y
/// envía la intención.
class CrearReservaSheet extends StatefulWidget {
  const CrearReservaSheet({
    super.key,
    required this.productoVarianteId,
    required this.productoNombre,
    required this.productoImagenUrl,
    required this.tallaNombre,
    required this.colorNombre,
    required this.sucursalId,
    required this.sucursalNombre,
    required this.token,
  });

  final int productoVarianteId;
  final String productoNombre;
  final String? productoImagenUrl;
  final String tallaNombre;
  final String colorNombre;
  final int sucursalId;
  final String sucursalNombre;
  final String token;

  @override
  State<CrearReservaSheet> createState() => _CrearReservaSheetState();
}

class _CrearReservaSheetState extends State<CrearReservaSheet> {
  final _service = CrearReservaService();
  late final List<DiaSeleccionable> _dias = proximosDias();

  String? _fechaSeleccionada;
  String? _horaSeleccionada;
  bool _confirmando = false;
  String? _errorMensaje;

  List<String> get _bloquesDisponibles {
    final fecha = _fechaSeleccionada;
    return fecha == null ? const [] : bloquesHorarioDisponibles(fecha);
  }

  bool get _puedeConfirmar =>
      _fechaSeleccionada != null && _horaSeleccionada != null && !_confirmando;

  void _seleccionarFecha(DiaSeleccionable dia) {
    if (dia.esDomingo) return;
    setState(() {
      _fechaSeleccionada = dia.iso;
      _horaSeleccionada = null;
      _errorMensaje = null;
    });
  }

  void _seleccionarHora(String hora) {
    setState(() {
      _horaSeleccionada = hora;
      _errorMensaje = null;
    });
  }

  Future<void> _confirmar() async {
    if (!_puedeConfirmar) return;
    setState(() {
      _confirmando = true;
      _errorMensaje = null;
    });
    try {
      final reserva = await _service.crear(
        productoVarianteId: widget.productoVarianteId,
        sucursalId: widget.sucursalId,
        fechaReserva: _fechaSeleccionada!,
        horaInicio: '${_horaSeleccionada!}:00',
        token: widget.token,
      );
      if (!mounted) return;
      Navigator.of(context).pop(reserva);
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _confirmando = false;
        _errorMensaje = e.message;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _confirmando = false;
        _errorMensaje = 'No se pudo crear la reserva. Inténtalo nuevamente.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final alturaMaxima = MediaQuery.of(context).size.height * 0.88;

    return SafeArea(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxHeight: alturaMaxima),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const _AsaArrastre(),
            Padding(
              padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, 0),
              child: Text(
                'Programar reserva',
                style: AppTextStyles.display.copyWith(fontSize: 20),
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _ProductoReservado(
                      nombre: widget.productoNombre,
                      imagenUrl: widget.productoImagenUrl,
                      tallaNombre: widget.tallaNombre,
                      colorNombre: widget.colorNombre,
                    ),
                    const SizedBox(height: AppSpacing.md),
                    _SucursalResumen(nombre: widget.sucursalNombre),
                    const SizedBox(height: AppSpacing.lg),
                    _EtiquetaSeccion(texto: 'Fecha'),
                    const SizedBox(height: AppSpacing.sm),
                    _SelectorFecha(
                      dias: _dias,
                      seleccionada: _fechaSeleccionada,
                      onSeleccionar: _seleccionarFecha,
                    ),
                    if (_fechaSeleccionada != null) ...[
                      const SizedBox(height: AppSpacing.lg),
                      _EtiquetaSeccion(texto: 'Horario'),
                      const SizedBox(height: AppSpacing.sm),
                      if (_bloquesDisponibles.isEmpty)
                        Text('Sin horarios disponibles ese día.', style: AppTextStyles.bodyMuted)
                      else
                        Wrap(
                          spacing: AppSpacing.sm,
                          runSpacing: AppSpacing.sm,
                          children: _bloquesDisponibles.map((bloque) {
                            return _HoraChip(
                              label: bloque,
                              seleccionado: bloque == _horaSeleccionada,
                              onTap: () => _seleccionarHora(bloque),
                            );
                          }).toList(),
                        ),
                    ],
                    if (_errorMensaje != null) ...[
                      const SizedBox(height: AppSpacing.md),
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        decoration: BoxDecoration(
                          color: AppColors.red.withValues(alpha: 0.08),
                          borderRadius: BorderRadius.circular(AppRadius.md),
                          border: Border.all(color: AppColors.red.withValues(alpha: 0.25)),
                        ),
                        child: Text(
                          _errorMensaje!,
                          style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy),
                        ),
                      ),
                    ],
                    const SizedBox(height: AppSpacing.lg),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, AppSpacing.lg),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _puedeConfirmar ? _confirmar : null,
                  child: Text(_confirmando ? 'RESERVANDO...' : 'CONFIRMAR RESERVA'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AsaArrastre extends StatelessWidget {
  const _AsaArrastre();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        width: 40,
        height: 4,
        margin: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
        decoration: BoxDecoration(
          color: AppColors.divider,
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
      ),
    );
  }
}

class _EtiquetaSeccion extends StatelessWidget {
  const _EtiquetaSeccion({required this.texto});

  final String texto;

  @override
  Widget build(BuildContext context) {
    return Text(texto.toUpperCase(), style: AppTextStyles.eyebrow.copyWith(color: AppColors.burgundy));
  }
}

/// Sección "1. Producto reservado" -- imagen pequeña ya cargada (nunca una
/// nueva), nombre y talla/color elegidos, para que el Cliente reconozca de
/// un vistazo QUÉ está reservando antes de elegir fecha/hora.
class _ProductoReservado extends StatelessWidget {
  const _ProductoReservado({
    required this.nombre,
    required this.imagenUrl,
    required this.tallaNombre,
    required this.colorNombre,
  });

  final String nombre;
  final String? imagenUrl;
  final String tallaNombre;
  final String colorNombre;

  @override
  Widget build(BuildContext context) {
    final variante = [colorNombre, if (tallaNombre.isNotEmpty) 'Talla $tallaNombre']
        .where((texto) => texto.isNotEmpty)
        .join(' · ');

    return Container(
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(AppRadius.sm),
            child: Container(
              width: 52,
              height: 52,
              color: AppColors.cream,
              child: imagenUrl != null
                  ? Image.network(
                      imagenUrl!,
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
                  nombre,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600),
                ),
                if (variante.isNotEmpty) ...[
                  const SizedBox(height: 2),
                  Text(variante, style: AppTextStyles.bodyMuted, maxLines: 1, overflow: TextOverflow.ellipsis),
                ],
              ],
            ),
          ),
        ],
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

/// Sección "2. Sucursal seleccionada" -- una sola línea, dato real ya
/// elegido en el detalle de producto (no hay pantalla de sucursales aparte).
class _SucursalResumen extends StatelessWidget {
  const _SucursalResumen({required this.nombre});

  final String nombre;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Icon(Icons.storefront_outlined, size: 15, color: AppColors.burgundy),
        const SizedBox(width: AppSpacing.xs),
        Expanded(
          child: Text(
            nombre,
            style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}

/// Sección "3. Fecha" -- franja horizontal deslizable de tarjetas compactas
/// (día + número), no una grilla que ocupa media pantalla. El domingo queda
/// visible pero deshabilitado ("No disponible") -- el Cliente debe VER que
/// ese día no atiende, nunca encontrarse con un hueco sin explicación.
class _SelectorFecha extends StatelessWidget {
  const _SelectorFecha({required this.dias, required this.seleccionada, required this.onSeleccionar});

  final List<DiaSeleccionable> dias;
  final String? seleccionada;
  final ValueChanged<DiaSeleccionable> onSeleccionar;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 64,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: dias.length,
        separatorBuilder: (_, _) => const SizedBox(width: AppSpacing.sm),
        itemBuilder: (context, index) {
          final dia = dias[index];
          return _DiaChip(
            dia: dia,
            seleccionado: dia.iso == seleccionada,
            onTap: () => onSeleccionar(dia),
          );
        },
      ),
    );
  }
}

class _DiaChip extends StatelessWidget {
  const _DiaChip({required this.dia, required this.seleccionado, required this.onTap});

  final DiaSeleccionable dia;
  final bool seleccionado;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final deshabilitado = dia.esDomingo;
    return GestureDetector(
      onTap: deshabilitado ? null : onTap,
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        width: 48,
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: seleccionado ? AppColors.red : AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: seleccionado ? AppColors.red : AppColors.divider),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              dia.etiqueta.split(' ').first,
              style: AppTextStyles.bodyMuted.copyWith(
                fontSize: 10,
                color: deshabilitado
                    ? AppColors.textSecondary.withValues(alpha: 0.5)
                    : (seleccionado ? AppColors.cream.withValues(alpha: 0.85) : AppColors.textSecondary),
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              dia.etiqueta.split(' ').last,
              style: AppTextStyles.body.copyWith(
                fontWeight: FontWeight.w700,
                color: deshabilitado
                    ? AppColors.textSecondary.withValues(alpha: 0.5)
                    : (seleccionado ? AppColors.cream : AppColors.charcoal),
              ),
            ),
            if (deshabilitado) ...[
              const SizedBox(height: 1),
              Container(width: 14, height: 1.4, color: AppColors.textSecondary.withValues(alpha: 0.4)),
            ],
          ],
        ),
      ),
    );
  }
}

class _HoraChip extends StatelessWidget {
  const _HoraChip({required this.label, required this.seleccionado, required this.onTap});

  final String label;
  final bool seleccionado;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
        decoration: BoxDecoration(
          color: seleccionado ? AppColors.red : AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.pill),
          border: Border.all(color: seleccionado ? AppColors.red : AppColors.divider),
        ),
        child: Text(
          label,
          style: AppTextStyles.body.copyWith(
            color: seleccionado ? AppColors.cream : AppColors.charcoal,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}
