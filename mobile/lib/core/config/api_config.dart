/// Configuración central de acceso al backend FastAPI.
///
/// Ningún otro archivo Dart debe escribir una URL del backend "a mano":
/// todos deben importar esta clase y construir sus rutas a partir de
/// [ApiConfig.apiBaseUrl].
class ApiConfig {
  ApiConfig._();

  /// Backend FastAPI corriendo en la máquina de desarrollo
  /// (`uvicorn app.main:app --host 0.0.0.0 --port 8000`, ver backend/README.md).
  ///
  /// 10.0.2.2 es el alias que el emulador de Android usa para llegar al
  /// "localhost" de la máquina host. Dentro del emulador, "localhost" se
  /// refiere al propio emulador, no al equipo de desarrollo -- por eso no
  /// se usa aquí.
  static const String _devBaseUrl = 'http://10.0.2.2:8000';

  /// Backend FastAPI en producción (Vercel). Es el MISMO backend que ya
  /// consume Angular -- ver frontend/web/src/environments/environment.ts.
  static const String _prodBaseUrl = 'https://fashionstore-api.vercel.app';

  /// Prefijo real de la API, tal como está definido en
  /// backend/app/core/config.py (Settings.API_V1_PREFIX).
  static const String apiPrefix = '/api/v1';

  /// Cambiar a `true` únicamente cuando se quiera apuntar Flutter al
  /// backend desplegado en vez del backend local.
  static const bool useProduction = true;

  static String get baseUrl => useProduction ? _prodBaseUrl : _devBaseUrl;

  /// Base completa a partir de la cual se arma cualquier endpoint,
  /// p. ej. '${ApiConfig.apiBaseUrl}/health' o '.../catalogo/productos'.
  static String get apiBaseUrl => '$baseUrl$apiPrefix';
}
