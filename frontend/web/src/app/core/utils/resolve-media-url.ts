import { environment } from '../../../environments/environment';

// Las URLs de imagen que devuelve FastAPI ya incluyen el prefijo de la API
// (ver backend/app/core/image_storage.py), p.ej. "/api/v1/media/productos/x.jpg".
// Aquí solo se resuelve el origen: en desarrollo, environment.apiUrl trae el
// host completo (http://localhost:8000/api/v1); en producción es una ruta
// relativa ("/api/v1") y Nginx ya reenvía "/api/" al backend.
export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) {
    return null;
  }
  const origin = environment.apiUrl.replace(/\/api\/v1\/?$/, '');
  return `${origin}${path}`;
}
