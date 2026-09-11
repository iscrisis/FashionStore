import 'package:flutter/material.dart';

import 'features/connection_test/connection_test_page.dart';

void main() {
  runApp(const FashionStoreApp());
}

/// Raíz de la app. Por ahora solo monta [ConnectionTestPage] para validar
/// Flutter -> FastAPI; el Home real del Cliente se implementa en una etapa
/// posterior, una vez confirmada la conexión.
class FashionStoreApp extends StatelessWidget {
  const FashionStoreApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FashionStore',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.black),
        useMaterial3: true,
      ),
      home: const ConnectionTestPage(),
    );
  }
}
