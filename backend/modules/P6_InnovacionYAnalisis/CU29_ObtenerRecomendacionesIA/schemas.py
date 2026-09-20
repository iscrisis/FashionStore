"""Contrato REST de CU29 -- Obtener recomendaciones mediante IA.

Un único endpoint conversacional (ver router.py). `historial` lo arma y
reenvía el propio frontend (Angular guarda la conversación solo en memoria
de la sesión, sin tabla propia -- ver __init__.py); el backend lo recorta a
las últimas interacciones antes de usarlo (ver service.py), nunca lo
persiste.

Los mismos contratos de salida los reutilizará el futuro cliente Flutter
(JSON puro, sin nada específico de Angular) -- mismo criterio que el resto
del proyecto (ver docstring de venta-presencial.model.ts, CU24).
"""

from typing import Literal

from pydantic import BaseModel, Field


class TurnoChatIn(BaseModel):
    rol: Literal["usuario", "asistente"]
    texto: str = Field(min_length=1, max_length=800)


class MensajeAsistenteRequest(BaseModel):
    # Límite razonable: ni Angular ni Flutter deberían mandar más que esto,
    # y protege a Gemini (y al propio backend) de un prompt desproporcionado.
    mensaje: str = Field(min_length=1, max_length=500)
    # Recortado otra vez en service.py a las últimas interacciones -- nunca
    # contexto ilimitado hacia Gemini.
    historial: list[TurnoChatIn] = Field(default_factory=list, max_length=12)


class ProductoRecomendadoOut(BaseModel):
    """Un producto REAL (siempre verificado contra PostgreSQL en este mismo
    request -- ver service.py) que el asistente muestra dentro del chat.

    precio_base/precio_final/en_promocion/porcentaje_descuento SIEMPRE
    calculados por P6_InnovacionYAnalisis/CU32_GestionarPromociones/
    precio_efectivo.py -- CU29 nunca vuelve a calcular un descuento.
    """

    id: int
    nombre: str
    imagen_principal_url: str | None
    precio_base: float
    precio_final: float
    en_promocion: bool
    porcentaje_descuento: float | None
    # Color/talla representativos -- solo se completan cuando la consulta
    # del Cliente los menciona explícitamente (ej. "chaqueta negra talla M");
    # en una recomendación general quedan en None (el producto puede tener
    # varias combinaciones, ver CU08).
    color: str | None
    talla: str | None
    # Texto ya armado ("Disponible en Mall Ventura.") -- Angular/Flutter lo
    # muestran tal cual, sin recalcular disponibilidad (ver
    # repository.DisponibilidadResumenRepository).
    disponibilidad_resumen: str | None


class MensajeAsistenteResponse(BaseModel):
    respuesta: str
    # Máximo 3 -- ver service.py:_MAX_PRODUCTOS_RESPUESTA ("no saturar el chat").
    productos: list[ProductoRecomendadoOut]
    tipo: Literal["recomendacion", "promocion", "disponibilidad", "conversacion", "fallback"]
    # True cuando la búsqueda real encontró más de los 3 que se muestran --
    # Angular/Flutter lo usan para el texto "Encontré más opciones en el
    # catálogo.", nunca para renderizar una cuarta card.
    hay_mas_resultados: bool
