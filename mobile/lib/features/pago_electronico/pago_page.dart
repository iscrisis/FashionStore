import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/network/api_client.dart';
import '../../core/storage/token_storage.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/media_url.dart';
import '../auth/auth_service.dart';
import '../auth/login_page.dart';
import '../auth/models/usuario_sesion.dart';
import '../compra_digital/models/compra_digital.dart';
import 'models/pago_electronico.dart';
import 'pago_electronico_service.dart';

enum _Estado { verificandoSesion, sinSesion, listo, preparando, esperandoPago, verificandoPago, error }

/// CU23 -- Procesar pago electrónico (Cliente). Se llega aquí SOLO desde
/// CU22 (`FinalizarCompraPage`, apenas `POST /compra-digital` responde) con
/// la `Venta` ya creada en PENDIENTE_PAGO -- nunca se re-consulta ni se
/// arma con datos nuevos, es exactamente la misma que devolvió CU22.
///
/// Flujo real: "PAGAR AHORA" pide una Checkout Session real a Stripe
/// (`POST /pagos/checkout`) y abre `checkout_url` en el navegador externo
/// (`url_launcher`, `LaunchMode.externalApplication` -- forma recomendada
/// por Stripe para Checkout Hosted en apps móviles). Nunca se arma un
/// formulario de tarjeta propio, nunca se guarda ni se muestra la URL al
/// Cliente.
///
/// VERIFICACIÓN MANUAL -- `success_url`/`cancel_url` las arma el backend
/// apuntando SIEMPRE a la web Angular (`settings.FRONTEND_URL` +
/// "/pago/resultado", ver CU23_ProcesarPagoElectronico/router.py:57-59),
/// nunca a esta app, así que Stripe no puede devolver al Cliente aquí
/// automáticamente -- resolverlo de raíz exigiría tocar ese backend
/// (fuera de esta autorización) o un deep link (explícitamente fuera de
/// alcance por ahora). En vez de eso, el Cliente vuelve él mismo y toca
/// "VERIFICAR PAGO".
///
/// Ese botón SÍ llama al endpoint real (`POST /pagos/verificar
/// {session_id}`) con el `session_id` REAL de Stripe -- sin pedírselo al
/// Cliente ni inventar nada: Stripe siempre incluye el id de la sesión
/// (`cs_test_...`/`cs_live_...`) como parte de la propia `checkout_url` que
/// ya recibimos al crear la sesión (formato estable y documentado de
/// Stripe Checkout, ver `_extraerSessionId` más abajo) -- Flutter solo lo
/// vuelve a leer de un dato que ya tenía, nunca lo solicita a mano.
class PagoPage extends StatefulWidget {
  const PagoPage({super.key, required this.venta});

  final VentaOut venta;

  @override
  State<PagoPage> createState() => _PagoPageState();
}

class _PagoPageState extends State<PagoPage> {
  final _authService = AuthService();
  final _service = PagoElectronicoService();

  _Estado _estado = _Estado.verificandoSesion;
  String? _token;
  String? _errorMensaje;
  String? _checkoutUrl;
  String? _sessionId;

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
    setState(() {
      _token = token;
      _estado = _Estado.listo;
    });
  }

  void _onLoginExitoso(UsuarioSesion usuario) {
    _iniciar();
  }

  Future<void> _pagarAhora() async {
    final token = _token;
    if (token == null || _estado == _Estado.preparando) return;

    setState(() {
      _estado = _Estado.preparando;
      _errorMensaje = null;
    });
    try {
      final sesion = await _service.crearCheckout(ventaId: widget.venta.id, token: token);
      if (!mounted) return;

      final sessionId = _extraerSessionId(sesion.checkoutUrl);
      if (sessionId == null) {
        // No debería pasar -- Stripe siempre incluye cs_... en la URL de
        // Checkout -- pero si el formato cambiara, es más honesto detenerse
        // acá (no se podría verificar el pago después) que abrir Stripe y
        // quedar sin forma de confirmarlo.
        setState(() {
          _estado = _Estado.error;
          _errorMensaje = 'No se pudo preparar el pago. Intenta nuevamente.';
        });
        return;
      }

      final abierto = await launchUrl(
        Uri.parse(sesion.checkoutUrl),
        mode: LaunchMode.externalApplication,
      );
      if (!mounted) return;
      if (!abierto) {
        setState(() {
          _estado = _Estado.error;
          _errorMensaje = 'No se pudo abrir el pago. Intenta nuevamente.';
        });
        return;
      }
      setState(() {
        _checkoutUrl = sesion.checkoutUrl;
        _sessionId = sessionId;
        _estado = _Estado.esperandoPago;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _estado = _Estado.error;
        _errorMensaje = _mensajeAmigable(e);
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _estado = _Estado.error;
        _errorMensaje = 'No se pudo abrir el pago. Intenta nuevamente.';
      });
    }
  }

  /// Reabre la MISMA Checkout Session -- no crea una nueva (evitaría
  /// duplicar filas de `Pago` en el backend sin necesidad, ver
  /// service.py:crear_checkout) -- útil si el Cliente cerró el navegador
  /// sin pagar y quiere reintentar.
  Future<void> _reabrirPago() async {
    final url = _checkoutUrl;
    if (url == null) return;
    final abierto = await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    if (!mounted || abierto) return;
    setState(() => _errorMensaje = 'No se pudo abrir el pago. Intenta nuevamente.');
  }

  Future<void> _verificarPago() async {
    final token = _token;
    final sessionId = _sessionId;
    if (token == null || sessionId == null || _estado == _Estado.verificandoPago) return;

    setState(() {
      _estado = _Estado.verificandoPago;
      _errorMensaje = null;
    });
    try {
      final venta = await _service.verificarPago(sessionId: sessionId, token: token);
      if (!mounted) return;

      await showDialog<void>(context: context, builder: (_) => _PagoConfirmadoDialog(venta: venta));
      if (!mounted) return;
      // CU23 termina aquí -- se vuelve al carrito (CU21). El backend ya
      // eliminó del carrito, dentro de la misma transacción que marcó la
      // Venta PAGADA, solo los items que formaron parte de esta compra (ver
      // service.py:verificar_pago) -- MiCarritoPage vuelve a consultar
      // `GET /carrito` apenas esta pantalla se cierra (ver
      // mi_carrito_page.dart, `_continuarCompra`), así que refleja ese
      // vaciado real sin que este archivo tenga que tocar el carrito.
      Navigator.of(context).pop();
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _estado = _Estado.esperandoPago;
        _errorMensaje = _mensajeAmigable(e);
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _estado = _Estado.esperandoPago;
        _errorMensaje = 'No se pudo verificar el pago. Revisa tu conexión e inténtalo de nuevo.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_estado == _Estado.sinSesion) {
      return LoginPage(onLoginExitoso: _onLoginExitoso);
    }
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(title: const Text('Pago')),
      body: SafeArea(child: _buildBody()),
    );
  }

  Widget _buildBody() {
    if (_estado == _Estado.verificandoSesion) {
      return const Center(child: CircularProgressIndicator(strokeWidth: 2));
    }

    final venta = widget.venta;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Pago de compra',
            style: AppTextStyles.display.copyWith(fontSize: 20),
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Código ${venta.codigoVenta}',
            style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: AppSpacing.xl),
          Text('Resumen', style: AppTextStyles.sectionTitle.copyWith(fontSize: 15)),
          const SizedBox(height: AppSpacing.sm),
          for (final detalle in venta.detalles)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: _DetalleVentaCard(detalle: detalle),
            ),
          const SizedBox(height: AppSpacing.xs),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Total', style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600)),
                Text('Bs ${venta.total.toStringAsFixed(2)}', style: AppTextStyles.price.copyWith(fontSize: 18)),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.xl),
          Text('Método de pago', style: AppTextStyles.sectionTitle.copyWith(fontSize: 15)),
          const SizedBox(height: AppSpacing.sm),
          const _MetodoPagoCard(),
          const SizedBox(height: AppSpacing.xl),
          if (_estado == _Estado.esperandoPago || _estado == _Estado.verificandoPago) ...[
            _EsperandoPago(),
            if (_errorMensaje != null) ...[
              const SizedBox(height: AppSpacing.md),
              _BannerError(mensaje: _errorMensaje!),
            ],
            const SizedBox(height: AppSpacing.md),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _estado == _Estado.verificandoPago ? null : _verificarPago,
                child: Text(_estado == _Estado.verificandoPago ? 'VERIFICANDO...' : 'VERIFICAR PAGO'),
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            Center(
              child: TextButton(
                onPressed: _estado == _Estado.verificandoPago ? null : _reabrirPago,
                child: const Text('Abrir el pago de nuevo'),
              ),
            ),
          ] else ...[
            if (_estado == _Estado.error && _errorMensaje != null) ...[
              _BannerError(mensaje: _errorMensaje!),
              const SizedBox(height: AppSpacing.md),
            ],
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _estado == _Estado.preparando ? null : _pagarAhora,
                child: Text(_estado == _Estado.preparando ? 'PREPARANDO PAGO...' : 'PAGAR AHORA'),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// Extrae el `session_id` real de Stripe (`cs_test_...`/`cs_live_...`) de la
/// propia `checkout_url` -- formato estable y documentado de Stripe
/// Checkout Hosted: la URL siempre trae el id de la sesión como parte de la
/// ruta. Ver docstring de [PagoPage] sobre por qué esto reemplaza pedirle
/// el `session_id` al Cliente a mano.
String? _extraerSessionId(String checkoutUrl) {
  final match = RegExp(r'cs_(?:test|live)_[A-Za-z0-9]+').firstMatch(checkoutUrl);
  return match?.group(0);
}

/// El backend de CU23 ya redacta sus mensajes en español profesional (ver
/// router.py: 404/422/503) -- `ApiClient` antepone un prefijo técnico
/// ("Error HTTP 422: ", "Recurso no encontrado: ", etc.) que esta pantalla
/// no debe mostrar. Se muestra solo lo que el backend redactó, nunca el
/// código HTTP ni JSON.
String _mensajeAmigable(ApiException e) {
  if (e.statusCode == null) {
    return 'No se pudo conectar. Revisa tu conexión e inténtalo de nuevo.';
  }
  final indice = e.message.indexOf(': ');
  return indice == -1 ? e.message : e.message.substring(indice + 2);
}

class _DetalleVentaCard extends StatelessWidget {
  const _DetalleVentaCard({required this.detalle});

  final VentaDetalleOut detalle;

  @override
  Widget build(BuildContext context) {
    final imagenUrl = MediaUrl.resolve(detalle.producto.imagenPrincipalUrl);

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
              width: 48,
              height: 48,
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
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Text(
            'Bs ${detalle.subtotal.toStringAsFixed(2)}',
            style: AppTextStyles.price.copyWith(fontSize: 14),
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
      child: Icon(Icons.checkroom_outlined, size: 18, color: AppColors.textSecondary),
    );
  }
}

/// Stripe (tarjeta) es el ÚNICO método real para CU23 (ver
/// Models/pago.py: `ProveedorPago.STRIPE` -- EFECTIVO/TARJETA/QR son
/// exclusivos del mostrador, CU25). No se muestra como una opción
/// seleccionable porque no hay ninguna otra entre la cual elegir -- mostrar
/// un selector de un solo ítem sería una pantalla administrativa, no una
/// app de moda.
class _MetodoPagoCard extends StatelessWidget {
  const _MetodoPagoCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.burgundy.withValues(alpha: 0.35)),
      ),
      child: Row(
        children: [
          const Icon(Icons.credit_card_outlined, size: 18, color: AppColors.burgundy),
          const SizedBox(width: AppSpacing.sm),
          Text('Tarjeta (Stripe)', style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

/// Estado tras abrir Stripe Checkout en el navegador externo -- nunca
/// muestra la URL, el `session_id` ni ningún detalle técnico (ver
/// [PagoPage]). No se presenta como error (el navegador SÍ se abrió) ni
/// como pago confirmado (eso solo lo dice `POST /pagos/verificar`, que
/// dispara el botón "VERIFICAR PAGO" que el propio [PagoPage] agrega debajo
/// de esta tarjeta).
class _EsperandoPago extends StatelessWidget {
  const _EsperandoPago();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        children: [
          Container(
            width: 48,
            height: 48,
            alignment: Alignment.center,
            decoration: const BoxDecoration(color: AppColors.gold, shape: BoxShape.circle),
            child: const Icon(Icons.storefront_outlined, color: AppColors.charcoal, size: 22),
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            'Completa tu pago en Stripe',
            textAlign: TextAlign.center,
            style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Cuando finalices, vuelve a la aplicación para confirmar tu compra.',
            textAlign: TextAlign.center,
            style: AppTextStyles.bodyMuted,
          ),
        ],
      ),
    );
  }
}

class _BannerError extends StatelessWidget {
  const _BannerError({required this.mensaje});

  final String mensaje;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.red.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.red.withValues(alpha: 0.25)),
      ),
      child: Text(mensaje, style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy)),
    );
  }
}

/// Confirmación final de CU23 tras `POST /pagos/verificar` exitoso --
/// muestra ÚNICAMENTE datos reales de `VentaPagadaOut` (código de venta,
/// total, estado): nada inventado (ni beneficios, ni descuentos, ni
/// puntos). `estado` siempre llega "PAGADA" en esta respuesta (el backend
/// no construye este objeto si no lo está, ver
/// CU23_ProcesarPagoElectronico/schemas.py:VentaPagadaOut) -- se muestra
/// capitalizado, sin inventar otro texto.
class _PagoConfirmadoDialog extends StatelessWidget {
  const _PagoConfirmadoDialog({required this.venta});

  final VentaPagadaOut venta;

  @override
  Widget build(BuildContext context) {
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
              'Pago realizado correctamente',
              textAlign: TextAlign.center,
              style: AppTextStyles.sectionTitle,
            ),
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
                        child: Text(
                          '${venta.sucursal.nombre} · ${venta.sucursal.ciudad}',
                          style: AppTextStyles.body,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Row(
                    children: [
                      const Icon(Icons.info_outline, size: 16, color: AppColors.burgundy),
                      const SizedBox(width: AppSpacing.sm),
                      Text(
                        venta.estado == 'PAGADA' ? 'Pagada' : venta.estado,
                        style: AppTextStyles.body,
                      ),
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
              child: ElevatedButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('LISTO'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
