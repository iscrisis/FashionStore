import 'package:shared_preferences/shared_preferences.dart';

/// Abstracción mínima para guardar el JWT que devolverá CU01 (Iniciar sesión)
/// cuando se implemente el login en Flutter.
///
/// Solo guarda el token recibido de FastAPI -- nunca contraseñas,
/// credenciales de PostgreSQL/Neon, ni ningún secreto del backend.
class TokenStorage {
  TokenStorage._();

  static const String _tokenKey = 'auth_token';

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  static Future<void> deleteToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
  }
}
