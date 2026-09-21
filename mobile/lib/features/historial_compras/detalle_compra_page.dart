import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/storage/token_storage.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/media_url.dart';
import '../../shared/widgets/async_state_message.dart';
import 'comprobante_venta_service.dart';
import 'compra_formato.dart';
import 'models/comprobante_venta.dart';

enum _Estado { cargando, listo, error }

/// Detalle de una compra -- CU27, reutilizando `GET /comprobantes/{venta_id}`
/// (CU31) tal cual el backend lo deja preparado para este fin (ver
/// comprobante_venta_service.dart). Se llega aquí SIEMPRE desde una tarjeta
/// de MisComprasPage, así que `ventaId`/`codigoVenta` ya son datos reales del
/// Cliente autenticado -- nunca se piden ni se adivinan aquí.
class DetalleCompraPage extends StatefulWidget {
  const DetalleCompraPage({super.key, required this.ventaId, required this.codigoVenta});

  final int ventaId;
  final String codigoVenta;

  @override
  State<DetalleCompraPage> createState() => _DetalleCompraPageState();
}

class _DetalleCompraPageState extends State<DetalleCompraPage> {
  final _service = ComprobanteVentaService();

  _Estado _estado = _Estado.cargando;
  ComprobanteVentaOut? _comprobante;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _estado = _Estado.cargando);
    final token = await TokenStorage.getToken();
    if (token == null) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
      return;
    }
    try {
      final comprobante = await _service.obtenerComprobante(ventaId: widget.ventaId, token: token);
      if (!mounted) return;
      setState(() {
        _comprobante = comprobante;
        _estado = _Estado.listo;
      });
    } on ApiException {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(title: Text('Compra ${widget.codigoVenta}')),
      body: SafeArea(child: _buildBody()),
    );
  }

  Widget _buildBody() {
    switch (_estado) {
      case _Estado.cargando:
        return const Center(child: CircularProgressIndicator(strokeWidth: 2));
      case _Estado.error:
        return Center(
          child: AsyncStateMessage(
            message: 'No se pudo cargar el detalle de esta compra.',
            icon: Icons.error_outline,
            onRetry: _cargar,
          ),
        );
      case _Estado.listo:
        return _DetalleContenido(comprobante: _comprobante!);
    }
  }
}

class _DetalleContenido extends StatelessWidget {
  const _DetalleContenido({required this.comprobante});

  final ComprobanteVentaOut comprobante;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      children: [
        _CabeceraCompra(comprobante: comprobante),
        const SizedBox(height: AppSpacing.lg),
        Text('PRODUCTOS', style: AppTextStyles.eyebrow.copyWith(color: AppColors.burgundy)),
        const SizedBox(height: AppSpacing.sm),
        Container(
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(AppRadius.lg),
            border: Border.all(color: AppColors.divider),
          ),
          padding: const EdgeInsets.all(AppSpacing.md),
          child: Column(
            children: [
              for (final detalle in comprobante.detalles) ...[
                _DetalleProductoRow(detalle: detalle),
                if (detalle != comprobante.detalles.last)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: AppSpacing.sm),
                    child: Divider(height: 1),
                  ),
              ],
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.lg),
        Container(
          padding: const EdgeInsets.all(AppSpacing.md),
          decoration: BoxDecoration(
            color: AppColors.burgundy,
            borderRadius: BorderRadius.circular(AppRadius.md),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Total', style: TextStyle(color: AppColors.cream, fontWeight: FontWeight.w600)),
              Text(
                'Bs ${comprobante.total.toStringAsFixed(2)}',
                style: const TextStyle(color: AppColors.cream, fontWeight: FontWeight.w700, fontSize: 18),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _CabeceraCompra extends StatelessWidget {
  const _CabeceraCompra({required this.comprobante});

  final ComprobanteVentaOut comprobante;

  @override
  Widget build(BuildContext context) {
    return Container(
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
                  comprobante.codigoVenta,
                  style: AppTextStyles.sectionTitle.copyWith(color: AppColors.burgundy),
                ),
              ),
              const _EstadoPagadoBadge(),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(formatearFechaHoraCompra(comprobante.fechaCreacion), style: AppTextStyles.bodyMuted),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: AppSpacing.sm),
            child: Divider(height: 1),
          ),
          Row(
            children: [
              const Icon(Icons.storefront_outlined, size: 16, color: AppColors.burgundy),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Text(
                  '${comprobante.sucursal.nombre} · ${comprobante.sucursal.ciudad}',
                  style: AppTextStyles.body,
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Row(
            children: [
              const Icon(Icons.place_outlined, size: 16, color: AppColors.burgundy),
              const SizedBox(width: AppSpacing.sm),
              Expanded(child: Text(comprobante.sucursal.direccion, style: AppTextStyles.bodyMuted)),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Row(
            children: [
              const Icon(Icons.local_shipping_outlined, size: 16, color: AppColors.burgundy),
              const SizedBox(width: AppSpacing.sm),
              Text('Compra ${etiquetaTipoVenta(comprobante.tipo).toLowerCase()}', style: AppTextStyles.bodyMuted),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Row(
            children: [
              const Icon(Icons.credit_card_outlined, size: 16, color: AppColors.burgundy),
              const SizedBox(width: AppSpacing.sm),
              Text(etiquetaMetodoPago(comprobante.metodoPago), style: AppTextStyles.bodyMuted),
            ],
          ),
        ],
      ),
    );
  }
}

/// El único estado real que este detalle puede llegar a mostrar -- CU31
/// rechaza cualquier Venta que no esté PAGADA antes de armar el comprobante
/// (ver service.py), así que nunca hace falta un switch de estados aquí.
class _EstadoPagadoBadge extends StatelessWidget {
  const _EstadoPagadoBadge();

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

class _DetalleProductoRow extends StatelessWidget {
  const _DetalleProductoRow({required this.detalle});

  final DetalleComprobanteOut detalle;

  @override
  Widget build(BuildContext context) {
    final imagenUrl = MediaUrl.resolve(detalle.producto.imagenPrincipalUrl);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.sm),
          child: Container(
            width: 56,
            height: 56,
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
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                detalle.producto.nombre,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600),
              ),
              Text(
                detalle.cantidad > 1
                    ? '${detalle.variante.color.nombre} · Talla ${detalle.variante.talla.nombre} · x${detalle.cantidad}'
                    : '${detalle.variante.color.nombre} · Talla ${detalle.variante.talla.nombre}',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: AppTextStyles.bodyMuted,
              ),
              Text(
                'Bs ${detalle.precioUnitario.toStringAsFixed(2)} c/u',
                style: AppTextStyles.bodyMuted.copyWith(fontSize: 11),
              ),
            ],
          ),
        ),
        const SizedBox(width: AppSpacing.sm),
        Text('Bs ${detalle.subtotal.toStringAsFixed(2)}', style: AppTextStyles.price),
      ],
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
