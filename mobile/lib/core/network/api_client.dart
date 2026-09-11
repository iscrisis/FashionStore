import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

/// Error de comunicación con el backend. Siempre trae un mensaje legible y,
/// cuando aplica, el código HTTP real devuelto por FastAPI -- así queda claro
/// si el fallo vino de la red, de Flutter o del propio backend.
class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => statusCode != null
      ? 'ApiException($statusCode): $message'
      : 'ApiException: $message';
}

/// Cliente HTTP único y reutilizable para consumir la API FastAPI existente.
///
/// Cualquier caso de uso futuro (catálogo, sucursales, login, etc.) debe
/// pasar por aquí en vez de llamar a `http` directamente, para no repetir
/// baseUrl, headers ni manejo de errores en cada pantalla.
class ApiClient {
  ApiClient({http.Client? httpClient, this.timeout = const Duration(seconds: 10)})
      : _httpClient = httpClient ?? http.Client();

  final http.Client _httpClient;
  final Duration timeout;

  Future<dynamic> get(String path, {Map<String, dynamic>? query, String? token}) {
    return _send(() => _httpClient
        .get(_buildUri(path, query), headers: _buildHeaders(token: token)));
  }

  Future<dynamic> post(String path, {Object? body, String? token}) {
    return _send(() => _httpClient.post(
          _buildUri(path),
          headers: _buildHeaders(token: token, hasBody: true),
          body: jsonEncode(body),
        ));
  }

  Future<dynamic> put(String path, {Object? body, String? token}) {
    return _send(() => _httpClient.put(
          _buildUri(path),
          headers: _buildHeaders(token: token, hasBody: true),
          body: jsonEncode(body),
        ));
  }

  Future<dynamic> patch(String path, {Object? body, String? token}) {
    return _send(() => _httpClient.patch(
          _buildUri(path),
          headers: _buildHeaders(token: token, hasBody: true),
          body: jsonEncode(body),
        ));
  }

  Future<dynamic> delete(String path, {String? token}) {
    return _send(() => _httpClient
        .delete(_buildUri(path), headers: _buildHeaders(token: token)));
  }

  Uri _buildUri(String path, [Map<String, dynamic>? query]) {
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return Uri.parse('${ApiConfig.apiBaseUrl}$normalizedPath').replace(
      queryParameters: query?.map((key, value) => MapEntry(key, '$value')),
    );
  }

  Map<String, String> _buildHeaders({String? token, bool hasBody = false}) {
    final headers = <String, String>{'Accept': 'application/json'};
    if (hasBody) headers['Content-Type'] = 'application/json';
    if (token != null) headers['Authorization'] = 'Bearer $token';
    return headers;
  }

  Future<dynamic> _send(Future<http.Response> Function() request) async {
    final http.Response response;
    try {
      response = await request().timeout(timeout);
    } on TimeoutException {
      throw ApiException(
        'Tiempo de espera agotado al contactar al servidor ($timeout). '
        '¿FastAPI está corriendo y accesible en la URL configurada?',
      );
    } on SocketException catch (e) {
      throw ApiException(
        'Sin conexión con el servidor (${e.message}). '
        'Verifica la red y que FastAPI esté corriendo en la URL configurada.',
      );
    } on http.ClientException catch (e) {
      throw ApiException('Error de red: ${e.message}');
    }

    dynamic decoded;
    if (response.body.isNotEmpty) {
      try {
        decoded = jsonDecode(response.body);
      } on FormatException {
        throw ApiException(
          'El servidor respondió con un cuerpo que no es JSON válido.',
          statusCode: response.statusCode,
        );
      }
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded;
    }

    final detail = (decoded is Map && decoded['detail'] != null)
        ? decoded['detail'].toString()
        : (response.reasonPhrase ?? 'Error desconocido');

    switch (response.statusCode) {
      case 400:
        throw ApiException('Solicitud inválida: $detail', statusCode: 400);
      case 401:
        throw ApiException('No autenticado: $detail', statusCode: 401);
      case 403:
        throw ApiException('No autorizado: $detail', statusCode: 403);
      case 404:
        throw ApiException('Recurso no encontrado: $detail', statusCode: 404);
      case 500:
        throw ApiException('Error interno del servidor: $detail', statusCode: 500);
      default:
        throw ApiException(
          'Error HTTP ${response.statusCode}: $detail',
          statusCode: response.statusCode,
        );
    }
  }
}
