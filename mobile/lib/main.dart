import 'package:flutter/material.dart';

import 'core/theme/app_theme.dart';
import 'features/pago_electronico/deep_link_service.dart';
import 'features/shell/app_shell.dart';

void main() {
  runApp(const FashionStoreApp());
}

/// `navigatorKey` global -- lo único que necesita [DeepLinkService] para
/// empujar la pantalla de resultado de CU23 (ver
/// features/pago_electronico/resultado_pago_page.dart) sobre lo que sea que
/// la app esté mostrando cuando Stripe redirige de vuelta con
/// `fashionstore://pago/resultado`, incluida la app recién arrancada en
/// frío desde ese mismo enlace.
final navigatorKey = GlobalKey<NavigatorState>();

/// Raíz de la app. Abre directamente en la Home pública (AppShell) -- el
/// login se pide más adelante, solo cuando el Cliente intente una acción
/// personal (ver arquitectura pública vs. autenticada en app_shell.dart).
class FashionStoreApp extends StatefulWidget {
  const FashionStoreApp({super.key});

  @override
  State<FashionStoreApp> createState() => _FashionStoreAppState();
}

class _FashionStoreAppState extends State<FashionStoreApp> {
  late final DeepLinkService _deepLinkService;

  @override
  void initState() {
    super.initState();
    _deepLinkService = DeepLinkService(navigatorKey: navigatorKey)..iniciar();
  }

  @override
  void dispose() {
    _deepLinkService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      navigatorKey: navigatorKey,
      title: 'FashionStore',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      home: const AppShell(),
    );
  }
}
