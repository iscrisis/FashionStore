import 'package:flutter/material.dart';

import '../../core/storage/token_storage.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../auth/auth_service.dart';
import '../auth/login_page.dart';
import '../auth/models/usuario_sesion.dart';
import 'models/pago_electronico.dart';
import 'pago_electronico_service.dart';

enum _Estado { verificandoSesion, sinSesion, verificando, confirmado, error }

/// CU23 -- Procesar pago electrónico (Cliente). Destino del deep link
/// `fashionstore://pago/resultado` (ver deep_link_service.dart) -- Stripe
/// vuelve aquí cuando el Checkout se creó con `"platform": "mobile"`.
///
/// Puede abrirse con la app ya corriendo o recién arrancando en frío desde
/// el enlace -- por eso NO depende de nada que haya vivido solo en la
/// memoria de `PagoPage` (ni la `Venta` completa, ni sus líneas): solo
/// necesita el `session_id` REAL que Stripe puso en la propia URL de
/// retorno para llamar `POST /pagos/verificar`, el mismo endpoint y el
/// mismo contrato que el botón "VERIFICAR PAGO" manual de `PagoPage`.
class ResultadoPagoPage extends StatefulWidget {
  const ResultadoPagoPage({super.key, required this.ventaId, this.sessionId, this.cancelado = false});

  final int ventaId;
  final String? sessionId;
  final bool cancelado;

  @override
  State<ResultadoPagoPage> createState() => _ResultadoPagoPageState();
}

class _ResultadoPagoPageState extends State<ResultadoPagoPage> {
  final _authService = AuthService();
  final _service = PagoElectronicoService();

  _Estado _estado = _Estado.verificandoSesion;
  VentaPagadaOut? _venta;

  @override
  void initState() {
    super.initState();
    _iniciar();
  }

  Future<void> _iniciar() async {
    final sesion = await _authService.sesionGuardada();
    if (!mounted) return;
    if (sesion == null) {
      setState(() => _estado = _Estado.sinSesion);
      return;
    }
    final token = await TokenStorage.getToken();
    if (!mounted) return;
    if (token == null) {
      setState(() => _estado = _Estado.sinSesion);
      return;
    }

    final sessionId = widget.sessionId;
    if (widget.cancelado || sessionId == null) {
      // El Cliente canceló Stripe Checkout, o el enlace llegó sin
      // session_id -- en ambos casos no hay nada real que verificar.
      setState(() => _estado = _Estado.error);
      return;
    }

    setState(() => _estado = _Estado.verificando);
    try {
      final venta = await _service.verificarPago(sessionId: sessionId, token: token);
      if (!mounted) return;
      setState(() {
        _venta = venta;
        _estado = _Estado.confirmado;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  void _onLoginExitoso(UsuarioSesion usuario) {
    _iniciar();
  }

  /// Vuelve al punto desde el que se llegó -- normalmente hasta AppShell,
  /// limpiando de paso `PagoPage`/`FinalizarCompraPage` si seguían en la
  /// pila (ver deep_link_service.dart: este enlace puede llegar con
  /// PagoPage todavía montada, o con la app recién arrancada en frío, sin
  /// nada debajo salvo AppShell). AppShell siempre existe como raíz
  /// (`home:` en main.dart), así que este `popUntil` nunca deja la pantalla
  /// en blanco.
  void _volver() {
    Navigator.of(context).popUntil((route) => route.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    if (_estado == _Estado.sinSesion) {
      return LoginPage(onLoginExitoso: _onLoginExitoso);
    }
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(title: const Text('Pago'), automaticallyImplyLeading: false),
      body: SafeArea(child: Center(child: SingleChildScrollView(child: _buildBody()))),
    );
  }

  Widget _buildBody() {
    switch (_estado) {
      case _Estado.verificandoSesion:
      case _Estado.verificando:
        return const _EstadoVerificando();
      case _Estado.confirmado:
        return _EstadoConfirmado(venta: _venta!, onListo: _volver);
      case _Estado.error:
        return _EstadoError(onReintentar: _iniciar, onCerrar: _volver);
      case _Estado.sinSesion:
        return const SizedBox.shrink();
    }
  }
}

class _EstadoVerificando extends StatelessWidget {
  const _EstadoVerificando();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.xl),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(strokeWidth: 2, color: AppColors.red),
          const SizedBox(height: AppSpacing.lg),
          Text('Confirmando tu pago...', style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

/// "Pago confirmado" -- solo datos reales de `VentaPagadaOut` (código de
/// venta, sucursal, estado, total): nada inventado (ni beneficios, ni
/// descuentos, ni puntos).
class _EstadoConfirmado extends StatelessWidget {
  const _EstadoConfirmado({required this.venta, required this.onListo});

  final VentaPagadaOut venta;
  final VoidCallback onListo;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.xl),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 64,
            height: 64,
            alignment: Alignment.center,
            decoration: const BoxDecoration(color: AppColors.burgundy, shape: BoxShape.circle),
            child: const Icon(Icons.check, color: AppColors.cream, size: 32),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Pago confirmado', style: AppTextStyles.sectionTitle, textAlign: TextAlign.center),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Código ${venta.codigoVenta}',
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
                Row(
                  children: [
                    const Icon(Icons.storefront_outlined, size: 16, color: AppColors.burgundy),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Text('${venta.sucursal.nombre} · ${venta.sucursal.ciudad}', style: AppTextStyles.body),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.sm),
                Row(
                  children: [
                    const Icon(Icons.info_outline, size: 16, color: AppColors.burgundy),
                    const SizedBox(width: AppSpacing.sm),
                    Text(venta.estado == 'PAGADA' ? 'Pagada' : venta.estado, style: AppTextStyles.body),
                  ],
                ),
                const SizedBox(height: AppSpacing.sm),
                Row(
                  children: [
                    const Icon(Icons.receipt_long_outlined, size: 16, color: AppColors.burgundy),
                    const SizedBox(width: AppSpacing.sm),
                    Text('Total: Bs ${venta.total.toStringAsFixed(2)}', style: AppTextStyles.body),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.xl),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(onPressed: onListo, child: const Text('LISTO')),
          ),
        ],
      ),
    );
  }
}

/// "No pudimos confirmar tu pago" -- nunca URLs, session_id, JSON ni
/// detalles internos, sin importar la causa real (cancelado, sesión aún no
/// pagada, error de red, etc.).
class _EstadoError extends StatelessWidget {
  const _EstadoError({required this.onReintentar, required this.onCerrar});

  final VoidCallback onReintentar;
  final VoidCallback onCerrar;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.xl),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 64,
            height: 64,
            alignment: Alignment.center,
            decoration: const BoxDecoration(color: AppColors.gold, shape: BoxShape.circle),
            child: const Icon(Icons.priority_high, color: AppColors.charcoal, size: 30),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('No pudimos confirmar tu pago', style: AppTextStyles.sectionTitle, textAlign: TextAlign.center),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Si crees que ya pagaste, inténtalo de nuevo en unos segundos.',
            textAlign: TextAlign.center,
            style: AppTextStyles.bodyMuted,
          ),
          const SizedBox(height: AppSpacing.xl),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(onPressed: onReintentar, child: const Text('REINTENTAR')),
          ),
          const SizedBox(height: AppSpacing.sm),
          TextButton(onPressed: onCerrar, child: const Text('Volver al carrito')),
        ],
      ),
    );
  }
}
