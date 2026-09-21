import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../../core/network/api_client.dart';
import '../../core/storage/token_storage.dart';
import 'models/usuario_sesion.dart';

/// Credenciales válidas, pero el rol del usuario no es CLIENTE -- FashionStore
/// Mobile es exclusivo para el actor Cliente (ver CU01, sección "mobile solo
/// cliente"). NO se guarda sesión en este caso: el backend no se modifica ni
/// se le pide que cambie el rol, Flutter simplemente rechaza la sesión móvil.
class RolNoPermitidoError implements Exception {}

/// CU02/CU04 -- ya existe una cuenta con ese correo (mismo caso que
/// CorreoYaRegistradoError en el backend, ver CU02_RegistrarCliente/
/// service.py y CU04_ActualizarPerfil/service.py -> 409 en ambos).
class CorreoYaRegistradoError implements Exception {}

/// No hay token guardado, o FastAPI respondió 401 al usarlo (expiró o ya no
/// es válido) -- en ambos casos la sesión ya se limpió (TokenStorage) y la
/// UI debe tratarlo exactamente como "no hay sesión", nunca como un error
/// de red genérico.
class SesionExpiradaError implements Exception {}

/// CU01 -- Iniciar sesión. Reutiliza el mismo `POST /auth/login` que ya usa
/// Angular (frontend/web/.../auth.service.ts): la respuesta ya trae el
/// usuario completo (incluido `rol`), así que no hace falta un endpoint
/// `/me` aparte para saber quién inició sesión ni con qué rol.
class AuthService {
  AuthService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  final ApiClient _apiClient;

  Future<UsuarioSesion> iniciarSesion({required String correo, required String password}) async {
    // DIAGNÓSTICO TEMPORAL (CU01) -- nunca imprime la contraseña, solo su
    // longitud, para confirmar que lo que sale de los TextFormField es
    // realmente lo que el usuario espera (ver bug de AutofillGroup ya
    // corregido). Quitar una vez confirmado el login real.
    debugPrint(
      '[CU01] Intentando login -- correo="$correo" (${correo.length} chars), '
      'password=${password.length} chars',
    );

    late final Map<String, dynamic> data;
    try {
      data = await _apiClient.post(
        '/auth/login',
        body: {'correo': correo, 'password': password},
      ) as Map<String, dynamic>;
    } on ApiException catch (e) {
      debugPrint('[CU01] Login FALLÓ -- statusCode=${e.statusCode} mensaje="${e.message}"');
      rethrow;
    }
    debugPrint('[CU01] Login OK -- usuario.rol="${data['usuario']?['rol']}"');

    final usuario = UsuarioSesion.fromJson(data['usuario'] as Map<String, dynamic>);

    if (!usuario.esCliente) {
      // Credenciales correctas, pero no es un Cliente -- no se persiste el
      // token: no debe quedar ninguna sesión móvil válida para este usuario.
      throw RolNoPermitidoError();
    }

    final token = data['access_token'] as String;
    await TokenStorage.saveToken(token);
    await TokenStorage.saveUsuario(jsonEncode(usuario.toJson()));
    return usuario;
  }

  /// Restaura la sesión guardada (si existe) al abrir la app -- sin llamar
  /// a ningún endpoint: el usuario ya se guardó completo en el login (ver
  /// TokenStorage). Si el JWT ya expiró (mismo claim `exp` que ya valida
  /// FastAPI en `decode_access_token`, ver app/core/security.py) o los datos
  /// guardados están corruptos, limpia la sesión y devuelve `null` -- Perfil
  /// verá que no hay usuario y mostrará Login directamente.
  Future<UsuarioSesion?> sesionGuardada() async {
    final token = await TokenStorage.getToken();
    final usuarioJson = await TokenStorage.getUsuario();
    if (token == null || usuarioJson == null) return null;

    if (_tokenExpirado(token)) {
      await TokenStorage.clearSession();
      return null;
    }

    try {
      return UsuarioSesion.fromJson(jsonDecode(usuarioJson) as Map<String, dynamic>);
    } catch (_) {
      await TokenStorage.clearSession();
      return null;
    }
  }

  Future<void> cerrarSesion() async {
    await TokenStorage.clearSession();
  }

  /// CU02 -- Registrar cliente. Reutiliza el mismo `POST /auth/register`
  /// que ya usa Angular (RegistrarCliente.submit() en
  /// registrar-cliente.ts): el backend exige `confirmar_password` como
  /// parte del propio contrato (ver RegistroClienteRequest, schemas.py --
  /// no es solo una validación de frontend), y el rol SIEMPRE lo fija el
  /// backend como CLIENTE -- el request no tiene ni tiene que tener un
  /// campo `rol`.
  ///
  /// No emite JWT ni guarda sesión: CU02 solo crea la cuenta, CU01 sigue
  /// siendo el único responsable de autenticar.
  Future<UsuarioSesion> registrarCliente({
    required String nombre,
    required String correo,
    required String telefono,
    required String password,
    required String confirmarPassword,
  }) async {
    try {
      final data = await _apiClient.post(
        '/auth/register',
        body: {
          'nombre': nombre,
          'correo': correo,
          'telefono': telefono,
          'password': password,
          'confirmar_password': confirmarPassword,
        },
      ) as Map<String, dynamic>;
      return UsuarioSesion.fromJson(data);
    } on ApiException catch (e) {
      if (e.statusCode == 409) {
        throw CorreoYaRegistradoError();
      }
      rethrow;
    }
  }

  /// CU04 -- obtener mi perfil (`GET /auth/me`). Requiere el JWT guardado;
  /// devuelve el usuario completo INCLUYENDO `telefono` (CU01/CU02 no lo
  /// traen) -- por eso Perfil llama esto al abrir, en vez de confiar
  /// únicamente en lo que ya guardó el login. Un 401 aquí significa que el
  /// token ya no es válido para FastAPI: se limpia la sesión y se traduce a
  /// [SesionExpiradaError], nunca a un error de red genérico.
  Future<UsuarioSesion> obtenerMiPerfil() async {
    final token = await TokenStorage.getToken();
    if (token == null) throw SesionExpiradaError();

    try {
      final data = await _apiClient.get('/auth/me', token: token) as Map<String, dynamic>;
      return UsuarioSesion.fromJson(data);
    } on ApiException catch (e) {
      if (e.statusCode == 401) {
        await TokenStorage.clearSession();
        throw SesionExpiradaError();
      }
      rethrow;
    }
  }

  /// CU04 -- actualizar mi perfil (`PUT /auth/me`). Solo nombre/correo/
  /// telefono -- el backend ni siquiera acepta un campo `rol` aquí (ver
  /// ActualizarPerfilRequest, schemas.py), así que Flutter no lo envía.
  /// Actualiza también la sesión guardada (TokenStorage) con la respuesta
  /// real del backend, para que un reinicio de la app no muestre datos
  /// obsoletos.
  Future<UsuarioSesion> actualizarMiPerfil({
    required String nombre,
    required String correo,
    required String telefono,
  }) async {
    final token = await TokenStorage.getToken();
    if (token == null) throw SesionExpiradaError();

    try {
      final data = await _apiClient.put(
        '/auth/me',
        token: token,
        body: {'nombre': nombre, 'correo': correo, 'telefono': telefono},
      ) as Map<String, dynamic>;
      final actualizado = UsuarioSesion.fromJson(data);
      await TokenStorage.saveUsuario(jsonEncode(actualizado.toJson()));
      return actualizado;
    } on ApiException catch (e) {
      if (e.statusCode == 401) {
        await TokenStorage.clearSession();
        throw SesionExpiradaError();
      }
      if (e.statusCode == 409) {
        throw CorreoYaRegistradoError();
      }
      rethrow;
    }
  }

  /// CU03 -- Recuperar contraseña (`POST /auth/forgot-password`). El
  /// backend SIEMPRE responde 200 con el mismo mensaje genérico exista o no
  /// la cuenta (ver PasswordResetService.solicitar, service.py -- así no se
  /// puede enumerar cuentas por correo); Flutter nunca debe intentar
  /// distinguir ese caso. Se devuelve el `message` real del backend en vez
  /// de uno hardcodeado en Flutter, para no arriesgarse a decir algo
  /// distinto de lo que el backend realmente hizo.
  Future<String> solicitarRecuperacion({required String correo}) async {
    // DIAGNÓSTICO TEMPORAL (CU03) -- el correo no es un dato sensible (a
    // diferencia de la contraseña), se registra tal cual para confirmar que
    // lo que sale del TextFormField es exactamente lo que el usuario espera.
    debugPrint('[CU03] Solicitando recuperación -- correo="$correo" (${correo.length} chars)');

    late final Map<String, dynamic> data;
    try {
      data = await _apiClient.post(
        '/auth/forgot-password',
        body: {'correo': correo},
      ) as Map<String, dynamic>;
    } on ApiException catch (e) {
      debugPrint('[CU03] forgot-password FALLÓ -- statusCode=${e.statusCode} mensaje="${e.message}"');
      rethrow;
    }
    debugPrint('[CU03] forgot-password OK -- message="${data['message']}"');

    return data['message'] as String? ??
        'Si existe una cuenta asociada a ese correo, recibirás instrucciones '
            'para restablecer tu contraseña.';
  }

  /// Lee el claim `exp` del JWT (segundo segmento, base64url) sin verificar
  /// la firma -- no hace falta: el backend ya la validó al emitirlo, esto
  /// solo evita mostrar una sesión que el propio backend rechazaría por
  /// vencida. Cualquier token ilegible se trata como expirado.
  bool _tokenExpirado(String token) {
    try {
      final partes = token.split('.');
      if (partes.length != 3) return true;
      final payloadJson = utf8.decode(base64Url.decode(base64Url.normalize(partes[1])));
      final payload = jsonDecode(payloadJson) as Map<String, dynamic>;
      final exp = payload['exp'];
      if (exp is! int) return false;
      final expiracion = DateTime.fromMillisecondsSinceEpoch(exp * 1000, isUtc: true);
      return DateTime.now().toUtc().isAfter(expiracion);
    } catch (_) {
      return true;
    }
  }
}
