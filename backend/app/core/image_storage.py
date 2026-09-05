"""Almacenamiento mínimo de imágenes subidas por el Administrador.

El proyecto no tenía ningún mecanismo de carga de archivos: esto NO es un CU,
es infraestructura transversal (como security.py o deps.py) que cualquier CU
que necesite imágenes reutiliza -- hoy CU08 (productos) y CU09 (categorías).

Guarda los archivos en disco bajo `backend/uploads/<subcarpeta>/` con un
nombre generado (nunca el nombre que envía el cliente) y devuelve la URL
pública bajo la que FastAPI los sirve (montada en app/main.py). PostgreSQL
solo guarda esa URL como texto -- nunca el archivo en sí.

Deliberadamente no usa Cloudinary/S3/Firebase ni ningún servicio externo. Si
el almacenamiento físico cambia más adelante (ej. a un bucket), solo esta
función necesita cambiar: los modelos de negocio (Producto, Categoria) solo
conocen una URL de texto.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

# backend/app/core/image_storage.py -> parents[2] == backend/
UPLOADS_ROOT = Path(__file__).resolve().parents[2] / "uploads"

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

    destino_dir = UPLOADS_ROOT / subcarpeta
    destino_dir.mkdir(parents=True, exist_ok=True)

    nombre_archivo = f"{uuid.uuid4().hex}{extension}"
    (destino_dir / nombre_archivo).write_bytes(contenido)

    return f"{settings.API_V1_PREFIX}/media/{subcarpeta}/{nombre_archivo}"


def eliminar_archivo_imagen(url: str | None) -> None:
    """Borra el archivo físico referenciado por una URL devuelta por
    guardar_archivo_imagen. Ignora URLs ajenas o archivos ya inexistentes
    (borrado idempotente: reemplazar una imagen no debe fallar si la
    anterior ya no está)."""
    if not url:
        return

    prefijo = f"{settings.API_V1_PREFIX}/media/"
    if not url.startswith(prefijo):
        return

    ruta_relativa = url[len(prefijo) :]
    ruta_absoluta = (UPLOADS_ROOT / ruta_relativa).resolve()

    if UPLOADS_ROOT.resolve() not in ruta_absoluta.parents:
        return

    ruta_absoluta.unlink(missing_ok=True)
