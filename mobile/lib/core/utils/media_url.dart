import '../config/api_config.dart';

/// Resuelve las URLs de imagen que devuelve FastAPI (ver
/// backend/app/core/image_storage.py): pueden venir relativas (servidas por
/// el propio backend, con prefijo /api/v1/media/...) o absolutas (Vercel
/// Blob en producción). Mismo criterio que
/// frontend/web/src/app/core/utils/resolve-media-url.ts -- una URL absoluta
/// ya es la URL pública final, solo las relativas se resuelven contra el
/// host de la API.
class MediaUrl {
  MediaUrl._();

  static String? resolve(String? path) {
    if (path == null || path.isEmpty) return null;
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    return '${ApiConfig.baseUrl}$path';
  }
}
