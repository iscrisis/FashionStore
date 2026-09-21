import 'package:shared_preferences/shared_preferences.dart';

/// Abstracción mínima para guardar la sesión de CU01 (Iniciar sesión):
/// el JWT y los datos públicos del usuario autenticado (id/nombre/correo/rol)
/// que ya devuelve `POST /auth/login` -- mismo criterio que
/// `frontend/web/.../auth.service.ts` (guarda token + usuario juntos para no
/// depender de un endpoint `/me` solo para restaurar sesión).
///
/// Guarda strings planos (el JSON del usuario ya viene serializado desde
/// quien lo llama) -- nunca contraseñas, credenciales de PostgreSQL/Neon, ni
/// ningún secreto del backend.
class TokenStorage {
  TokenStorage._();

  static const String _tokenKey = 'auth_token';
  static const String _usuarioKey = 'auth_usuario';

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

  static Future<void> saveUsuario(String usuarioJson) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_usuarioKey, usuarioJson);
  }

  static Future<String?> getUsuario() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_usuarioKey);
  }

  static Future<void> deleteUsuario() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_usuarioKey);
  }

  /// Limpia token + usuario juntos -- usado tanto por "Cerrar sesión" como
  /// por cualquier 401 futuro que invalide la sesión actual.
  static Future<void> clearSession() async {
    await deleteToken();
    await deleteUsuario();
  }
}
