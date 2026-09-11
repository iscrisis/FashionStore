import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';

/// Pantalla TEMPORAL, solo para esta tarea: comprobar que Flutter puede
/// llegar al FastAPI existente. No es el Home definitivo de la app --
/// se reemplazará cuando se implementen los casos de uso reales del Cliente.
class ConnectionTestPage extends StatefulWidget {
  const ConnectionTestPage({super.key});

  @override
  State<ConnectionTestPage> createState() => _ConnectionTestPageState();
}

enum _Status { loading, success, error }

class _ConnectionTestPageState extends State<ConnectionTestPage> {
  final ApiClient _apiClient = ApiClient();

  _Status _status = _Status.loading;
  Object? _data;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _checkConnection();
  }

  Future<void> _checkConnection() async {
    setState(() {
      _status = _Status.loading;
      _errorMessage = null;
    });

    try {
      // GET /api/v1/health -- endpoint público y real de backend/app/routers/health.py.
      final result = await _apiClient.get('/health');
      setState(() {
        _data = result;
        _status = _Status.success;
      });
    } on ApiException catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _status = _Status.error;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Prueba de conexión FastAPI')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: _buildBody(),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _checkConnection,
        tooltip: 'Reintentar',
        child: const Icon(Icons.refresh),
      ),
    );
  }

  Widget _buildBody() {
    switch (_status) {
      case _Status.loading:
        return const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Conectando con FastAPI...'),
          ],
        );
      case _Status.success:
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.check_circle, color: Colors.green, size: 48),
            const SizedBox(height: 16),
            const Text('Conexión exitosa con FastAPI'),
            const SizedBox(height: 8),
            Text('$_data', textAlign: TextAlign.center),
          ],
        );
      case _Status.error:
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error, color: Colors.red, size: 48),
            const SizedBox(height: 16),
            const Text('Error al conectar con FastAPI'),
            const SizedBox(height: 8),
            Text(_errorMessage ?? '', textAlign: TextAlign.center),
          ],
        );
    }
  }
}
