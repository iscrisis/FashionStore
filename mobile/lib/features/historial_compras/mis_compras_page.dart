import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/storage/token_storage.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../shared/widgets/async_state_message.dart';
import '../../shared/widgets/primary_button.dart';
import 'compra_formato.dart';
import 'detalle_compra_page.dart';
import 'historial_compras_service.dart';
import 'models/historial_compra.dart';

enum _Estado { cargando, listo, vacio, error }

/// CU27 -- Consultar historial de compras (Cliente). Se llega aquí SIEMPRE
/// desde el tab Perfil, con sesión ya verificada por PerfilPage -- por eso,
/// a diferencia de MisReservasPage, no necesita un estado "sin sesión"
/// propio: si el token ya no es válido (401), se trata como error y se deja
/// que el Cliente reintente o vuelva a Perfil, donde sí se resuelve la
/// sesión expirada.
///
/// Filtros (Desde/Hasta/Código) calcados de `FiltroHistorial` en Angular
/// (frontend/web/.../historial-compras/filtro-historial/filtro-historial.ts)
/// -- mismos 3 parámetros opcionales, misma validación local de "Desde" <=
/// "Hasta" (solo feedback inmediato: la autoridad real es FastAPI, ver
/// RangoFechaInvalidoError en el backend).
class MisComprasPage extends StatefulWidget {
  const MisComprasPage({super.key});

  @override
  State<MisComprasPage> createState() => _MisComprasPageState();
}

class _MisComprasPageState extends State<MisComprasPage> {
  final _service = HistorialComprasService();
  final _codigoController = TextEditingController();

  _Estado _estado = _Estado.cargando;
  List<VentaHistorialOut> _compras = [];

  DateTime? _desde;
  DateTime? _hasta;

  bool get _rangoInvalido => _desde != null && _hasta != null && _desde!.isAfter(_hasta!);

  @override
  void initState() {
    super.initState();
    _cargarCompras();
  }

  @override
  void dispose() {
    _codigoController.dispose();
    super.dispose();
  }

  Future<void> _cargarCompras() async {
    setState(() => _estado = _Estado.cargando);
    final token = await TokenStorage.getToken();
    if (token == null) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
      return;
    }
    try {
      final compras = await _service.listarMias(
        token: token,
        desde: _desde != null ? formatearFechaParaApi(_desde!) : null,
        hasta: _hasta != null ? formatearFechaParaApi(_hasta!) : null,
        codigoVenta: _codigoController.text.trim(),
      );
      if (!mounted) return;
      setState(() {
        _compras = compras;
        _estado = compras.isEmpty ? _Estado.vacio : _Estado.listo;
      });
    } on ApiException {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  Future<void> _seleccionarFecha({required bool esDesde}) async {
    final inicial = (esDesde ? _desde : _hasta) ?? DateTime.now();
    final seleccionada = await showDatePicker(
      context: context,
      initialDate: inicial,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(colorScheme: const ColorScheme.light(primary: AppColors.burgundy)),
          child: child!,
        );
      },
    );
    if (seleccionada == null) return;
    setState(() {
      if (esDesde) {
        _desde = seleccionada;
      } else {
        _hasta = seleccionada;
      }
    });
  }

  void _aplicarFiltro() {
    if (_rangoInvalido) return;
    _cargarCompras();
  }

  void _limpiarFiltro() {
    setState(() {
      _desde = null;
      _hasta = null;
      _codigoController.clear();
    });
    _cargarCompras();
  }

  void _abrirDetalle(VentaHistorialOut compra) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => DetalleCompraPage(ventaId: compra.ventaId, codigoVenta: compra.codigoVenta),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(title: const Text('Mis compras')),
      body: SafeArea(
        child: Column(
          children: [
            _FiltroHistorial(
              desde: _desde,
              hasta: _hasta,
              codigoController: _codigoController,
              rangoInvalido: _rangoInvalido,
              onSeleccionarFecha: _seleccionarFecha,
              onFiltrar: _aplicarFiltro,
              onLimpiar: _limpiarFiltro,
            ),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    switch (_estado) {
      case _Estado.cargando:
        return const Center(child: CircularProgressIndicator(strokeWidth: 2));
      case _Estado.error:
        return Center(
          child: AsyncStateMessage(
            message: 'No se pudieron cargar tus compras.',
            icon: Icons.error_outline,
            onRetry: _cargarCompras,
          ),
        );
      case _Estado.vacio:
        return _EstadoVacio(onRefrescar: _cargarCompras);
      case _Estado.listo:
        return RefreshIndicator(
          color: AppColors.red,
          onRefresh: _cargarCompras,
          child: ListView.separated(
            padding: const EdgeInsets.fromLTRB(
              AppSpacing.lg,
              AppSpacing.md,
              AppSpacing.lg,
              AppSpacing.lg,
            ),
            itemCount: _compras.length,
            separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.md),
            itemBuilder: (context, index) {
              final compra = _compras[index];
              return _CompraCard(compra: compra, onTap: () => _abrirDetalle(compra));
            },
          ),
        );
    }
  }
}

/// Barra de filtros -- Desde / Hasta (selector de fecha nativo) y Código,
/// con Filtrar/Limpiar. Misma lógica que `app-filtro-historial` en Angular,
/// adaptada a controles móviles (selector de fecha en vez de `<input
/// type="date">`).
class _FiltroHistorial extends StatelessWidget {
  const _FiltroHistorial({
    required this.desde,
    required this.hasta,
    required this.codigoController,
    required this.rangoInvalido,
    required this.onSeleccionarFecha,
    required this.onFiltrar,
    required this.onLimpiar,
  });

  final DateTime? desde;
  final DateTime? hasta;
  final TextEditingController codigoController;
  final bool rangoInvalido;
  final void Function({required bool esDesde}) onSeleccionarFecha;
  final VoidCallback onFiltrar;
  final VoidCallback onLimpiar;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.md, AppSpacing.lg, 0),
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: _SelectorFecha(label: 'Desde', fecha: desde, onTap: () => onSeleccionarFecha(esDesde: true)),
              ),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: _SelectorFecha(label: 'Hasta', fecha: hasta, onTap: () => onSeleccionarFecha(esDesde: false)),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          TextField(
            controller: codigoController,
            textCapitalization: TextCapitalization.characters,
            style: AppTextStyles.body,
            decoration: InputDecoration(
              labelText: 'Código',
              hintText: 'VT-00000',
              filled: true,
              fillColor: AppColors.cream,
              contentPadding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppRadius.sm),
                borderSide: BorderSide.none,
              ),
            ),
            onSubmitted: (_) => onFiltrar(),
          ),
          if (rangoInvalido) ...[
            const SizedBox(height: AppSpacing.xs),
            Text(
              '"Desde" no puede ser posterior a "Hasta".',
              style: AppTextStyles.bodyMuted.copyWith(color: AppColors.red),
            ),
          ],
          const SizedBox(height: AppSpacing.sm),
          Row(
            children: [
              Expanded(
                child: PrimaryButton(
                  label: 'FILTRAR',
                  onPressed: rangoInvalido ? null : onFiltrar,
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              TextButton(onPressed: onLimpiar, child: const Text('Limpiar')),
            ],
          ),
        ],
      ),
    );
  }
}

class _SelectorFecha extends StatelessWidget {
  const _SelectorFecha({required this.label, required this.fecha, required this.onTap});

  final String label;
  final DateTime? fecha;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: AppSpacing.sm),
        decoration: BoxDecoration(
          color: AppColors.cream,
          borderRadius: BorderRadius.circular(AppRadius.sm),
        ),
        child: Row(
          children: [
            const Icon(Icons.calendar_today_outlined, size: 14, color: AppColors.burgundy),
            const SizedBox(width: AppSpacing.xs),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: AppTextStyles.bodyMuted.copyWith(fontSize: 10)),
                  Text(
                    fecha != null ? formatearFechaCompra(fecha!.toIso8601String()) : '--/--/----',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600, fontSize: 12),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// "Sin compras" -- mismo lenguaje visual que el estado vacío de Reservas
/// (ícono en círculo + título + mensaje), sin inventar contadores ni datos.
class _EstadoVacio extends StatelessWidget {
  const _EstadoVacio({required this.onRefrescar});

  final Future<void> Function() onRefrescar;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      color: AppColors.red,
      onRefresh: onRefrescar,
      child: LayoutBuilder(
        builder: (context, constraints) {
          return SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: ConstrainedBox(
              constraints: BoxConstraints(minHeight: constraints.maxHeight),
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 72,
                        height: 72,
                        decoration: const BoxDecoration(color: AppColors.surface, shape: BoxShape.circle),
                        child: const Icon(
                          Icons.shopping_bag_outlined,
                          size: 30,
                          color: AppColors.burgundy,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      Text('Aún no tienes compras', style: AppTextStyles.sectionTitle, textAlign: TextAlign.center),
                      const SizedBox(height: AppSpacing.sm),
                      Text(
                        'Cuando realices una compra aparecerá aquí.',
                        style: AppTextStyles.bodyMuted,
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

/// Tarjeta de una compra -- código + estado, fecha, sucursal, tipo, método
/// de pago y total, con acceso al detalle completo (CU31 reutilizado).
/// Mismos campos y mismas etiquetas que `compra-card` en Angular
/// (historial-compras.html): código, fecha, sucursal, tipo, método de pago,
/// total y "Ver".
class _CompraCard extends StatelessWidget {
  const _CompraCard({required this.compra, required this.onTap});

  final VentaHistorialOut compra;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(color: AppColors.divider),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    compra.codigoVenta,
                    style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy, fontWeight: FontWeight.w600),
                  ),
                ),
                const _EstadoPagadaBadge(),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: [
                const Icon(Icons.event_outlined, size: 14, color: AppColors.burgundy),
                const SizedBox(width: AppSpacing.xs),
                Text(formatearFechaCompra(compra.fecha), style: AppTextStyles.bodyMuted),
              ],
            ),
            const SizedBox(height: 2),
            Row(
              children: [
                const Icon(Icons.storefront_outlined, size: 14, color: AppColors.burgundy),
                const SizedBox(width: AppSpacing.xs),
                Expanded(
                  child: Text(
                    compra.sucursal.nombre,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTextStyles.bodyMuted,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 2),
            Row(
              children: [
                const Icon(Icons.local_shipping_outlined, size: 14, color: AppColors.burgundy),
                const SizedBox(width: AppSpacing.xs),
                Text(
                  'Compra ${etiquetaTipoVenta(compra.tipo).toLowerCase()}',
                  style: AppTextStyles.bodyMuted,
                ),
                const SizedBox(width: AppSpacing.sm),
                const Icon(Icons.credit_card_outlined, size: 14, color: AppColors.burgundy),
                const SizedBox(width: AppSpacing.xs),
                Text(etiquetaMetodoPago(compra.metodoPago), style: AppTextStyles.bodyMuted),
              ],
            ),
            if (compra.leyendaPostventa != null) ...[
              const SizedBox(height: AppSpacing.xs),
              Row(
                children: [
                  const Icon(Icons.info_outline, size: 14, color: AppColors.gold),
                  const SizedBox(width: AppSpacing.xs),
                  Expanded(
                    child: Text(
                      compra.leyendaPostventa!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTextStyles.bodyMuted.copyWith(color: AppColors.charcoal),
                    ),
                  ),
                ],
              ),
            ],
            const Padding(
              padding: EdgeInsets.symmetric(vertical: AppSpacing.sm),
              child: Divider(height: 1),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Bs ${compra.total.toStringAsFixed(2)}', style: AppTextStyles.price),
                Row(
                  children: [
                    Text('Ver detalle', style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy)),
                    const Icon(Icons.chevron_right, size: 18, color: AppColors.burgundy),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Todas las filas de CU27 son SIEMPRE de una Venta PAGADA (el backend nunca
/// lista PENDIENTE_PAGO aquí, ver service.py) -- por eso el badge es fijo,
/// sin inventar un switch de estados que el backend no produce en este
/// endpoint. `leyendaPostventa` (si existe) se muestra aparte, como aviso
/// adicional, nunca como un estado nuevo de la Venta.
class _EstadoPagadaBadge extends StatelessWidget {
  const _EstadoPagadaBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: AppColors.burgundy, borderRadius: BorderRadius.circular(AppRadius.pill)),
      child: const Text(
        'Pagada',
        style: TextStyle(color: AppColors.cream, fontWeight: FontWeight.w600, fontSize: 11),
      ),
    );
  }
}
