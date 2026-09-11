import { environment } from '../../../environments/environment';

// Las URLs de imagen que devuelve FastAPI pueden venir en dos formas (ver
// backend/app/core/image_storage.py):
// - relativas, con el prefijo de la API, p.ej. "/api/v1/media/productos/x.jpg"
//   (desarrollo local, servidas por el propio FastAPI); o
// - absolutas HTTPS, p.ej. "https://xxx.public.blob.vercel-storage.com/..."
//   (producción en Vercel, Vercel Blob las sirve directamente).
// Una URL absoluta ya es la URL pública final y no debe concatenarse con el
// host de la API -- solo las relativas necesitan resolverse contra
// environment.apiUrl (host completo de FastAPI, ver environment.ts).
export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) {
    return null;
  }
  if (/^https?:\/\//i.test(path)) {
    return path;
  }
  const origin = environment.apiUrl.replace(/\/api\/v1\/?$/, '');
  return `${origin}${path}`;
}
