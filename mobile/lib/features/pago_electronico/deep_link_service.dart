import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter/material.dart';

import 'resultado_pago_page.dart';

/// Captura el retorno de Stripe Checkout hacia CU23 en modo móvil --
/// `fashionstore://pago/resultado?venta_id=...&session_id=...` (pago
/// completado) o `...&cancelado=1` (el Cliente cerró/canceló Stripe Checkout
/// sin pagar) -- ver backend/modules/P5_ComprasVentasYPagos/
/// CU23_ProcesarPagoElectronico/router.py (arma esa URL SOLO cuando
/// `POST /pagos/checkout` se llamó con `"platform": "mobile"`, ver
/// pago_electronico_service.dart) y el esquema registrado en
/// android/app/src/main/AndroidManifest.xml + ios/Runner/Info.plist.
///
/// Se instancia UNA sola vez, en la raíz de la app (ver main.dart) -- nunca
/// dentro de PagoPage, porque el enlace puede llegar con esa pantalla ya
/// cerrada, o con la app recién arrancando en frío desde el propio enlace
/// (el Cliente cerró FashionStore Mobile mientras pagaba en Stripe). Usa el
/// `navigatorKey` global para empujar [ResultadoPagoPage] sobre lo que sea
/// que esté mostrando la app en ese momento.
///
/// PagoPage conserva su botón manual "VERIFICAR PAGO" como respaldo: si por
/// lo que sea (un navegador que no honra el esquema, el Cliente cambia de
/// app justo antes de que Stripe redirija) este enlace no llegara a
/// dispararse, el Cliente igual puede confirmar su pago a mano.
class DeepLinkService {
  DeepLinkService({required this.navigatorKey});

  final GlobalKey<NavigatorState> navigatorKey;
  final _appLinks = AppLinks();
  StreamSubscription<Uri>? _subscription;

  void iniciar() {
    // Enlace que abrió la app en frío (proceso recién arrancado) -- si no
    // hay ninguno, `getInitialLink` simplemente resuelve null.
    _appLinks.getInitialLink().then(_manejar);
    // Enlaces mientras la app ya está corriendo (primer o segundo plano).
    _subscription = _appLinks.uriLinkStream.listen(_manejar);
  }

  void _manejar(Uri? uri) {
    if (uri == null || uri.scheme != 'fashionstore' || uri.host != 'pago') return;
    if (uri.pathSegments.isEmpty || uri.pathSegments.first != 'resultado') return;

    final ventaId = int.tryParse(uri.queryParameters['venta_id'] ?? '');
    if (ventaId == null) return;
    final sessionId = uri.queryParameters['session_id'];
    final cancelado = uri.queryParameters['cancelado'] == '1';

    navigatorKey.currentState?.push(
      MaterialPageRoute(
        builder: (_) => ResultadoPagoPage(ventaId: ventaId, sessionId: sessionId, cancelado: cancelado),
      ),
    );
  }

  void dispose() {
    _subscription?.cancel();
  }
}
