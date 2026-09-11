"""Almacenamiento mínimo de imágenes subidas por el Administrador.

El proyecto no tenía ningún mecanismo de carga de archivos: esto NO es un CU,
es infraestructura transversal (como security.py o deps.py) que cualquier CU
que necesite imágenes reutiliza -- hoy CU08 (productos) y CU09 (categorías).

En desarrollo local, guarda los archivos en disco bajo
`backend/uploads/<subcarpeta>/` con un nombre generado (nunca el nombre que
envía el cliente) y devuelve la URL relativa bajo la que FastAPI los sirve
(montada en app/main.py).

En Vercel (VERCEL=1) el filesystem del despliegue es de solo lectura salvo
/tmp, y /tmp es efímero: se pierde entre invocaciones frías y no se comparte
entre instancias, así que cualquier imagen guardada ahí desaparece poco
después de subirse. Por eso en ese entorno las imágenes se suben a Vercel
Blob (almacenamiento persistente) y se guarda su URL HTTPS pública.

En ambos casos PostgreSQL solo guarda una URL como texto -- nunca el archivo
en sí -- y los modelos de negocio (Producto, Categoria) no conocen el origen
físico de esa URL.
"""

import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

# backend/app/core/image_storage.py -> parents[2] == backend/
UPLOADS_ROOT = (
    Path("/tmp/uploads")
    if os.getenv("VERCEL")
    else Path(__file__).resolve().parents[2] / "uploads"
)


def _usar_almacenamiento_persistente() -> bool:
    """En Vercel el disco es efímero: ahí se usa Vercel Blob en vez de disco."""
    return bool(os.getenv("VERCEL"))


MAX_TAMANO_BYTES = 5 * 1024 * 1024  # 5 MB

_EXTENSION_POR_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class ImagenInvalidaError(Exception):
    """El archivo no es una imagen en un formato admitido (JPG, JPEG, PNG, WEBP)."""


class ImagenDemasiadoGrandeError(Exception):
    """El archivo supera el tamaño máximo permitido."""


def guardar_archivo_imagen(subcarpeta: str, archivo: UploadFile, contenido: bytes) -> str:
    """Valida y guarda una imagen ya leída en memoria; devuelve su URL pública."""
    extension = _EXTENSION_POR_CONTENT_TYPE.get((archivo.content_type or "").lower())
    if extension is None:
        raise ImagenInvalidaError

    if len(contenido) > MAX_TAMANO_BYTES:
        raise ImagenDemasiadoGrandeError

    nombre_archivo = f"{uuid.uuid4().hex}{extension}"

    if _usar_almacenamiento_persistente():
        # Import diferido: este módulo pesa (websockets, etc.) y no hace
        # falta cargarlo en desarrollo local, donde nunca se ejecuta esta rama.
        from vercel.blob import put as blob_put

        resultado = blob_put(
            f"{subcarpeta}/{nombre_archivo}",
            contenido,
            access="public",
            content_type=archivo.content_type,
            add_random_suffix=False,
        )
        return resultado.url

    destino_dir = UPLOADS_ROOT / subcarpeta
    destino_dir.mkdir(parents=True, exist_ok=True)
    (destino_dir / nombre_archivo).write_bytes(contenido)

    return f"{settings.API_V1_PREFIX}/media/{subcarpeta}/{nombre_archivo}"


def eliminar_archivo_imagen(url: str | None) -> None:
    """Borra el archivo referenciado por una URL devuelta por
    guardar_archivo_imagen (en disco local o en Vercel Blob). Ignora URLs
    ajenas o archivos ya inexistentes (borrado idempotente: reemplazar una
    imagen no debe fallar si la anterior ya no está)."""
    if not url:
        return

    if url.startswith("http://") or url.startswith("https://"):
        from vercel.blob import delete as blob_delete

        blob_delete(url)
        return

    prefijo = f"{settings.API_V1_PREFIX}/media/"
    if not url.startswith(prefijo):
        return

    ruta_relativa = url[len(prefijo) :]
    ruta_absoluta = (UPLOADS_ROOT / ruta_relativa).resolve()

    if UPLOADS_ROOT.resolve() not in ruta_absoluta.parents:
        return

    ruta_absoluta.unlink(missing_ok=True)
