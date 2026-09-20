"""CU29 -- Obtener recomendaciones mediante IA (Cliente/Invitado), PK06.

Asistente conversacional de FashionStore: interpreta la consulta del
Cliente con Gemini, consulta PostgreSQL a través de los repositorios y
servicios YA existentes (catálogo de CU11, precio efectivo de CU32, stock de
CU12/CU14, historial de compras de CU27) y devuelve una respuesta en
lenguaje natural junto con, como máximo, 3 productos REALES.

Arquitectura obligatoria (nunca al revés):

    Angular -> FastAPI (este paquete) -> PostgreSQL / servicios existentes
             -> Gemini -> FastAPI valida -> Angular

Gemini JAMÁS recibe credenciales de base de datos, nunca ejecuta ni genera
SQL, y nunca decide qué productos se devuelven -- solo interpreta texto
(gemini_client.interpretar_consulta) y redacta la respuesta final en
lenguaje natural a partir del contexto comercial real que arma service.py
(gemini_client.generar_respuesta). El array `productos` de la respuesta
SIEMPRE sale de una consulta de este mismo request a PostgreSQL -- ver
service.py.

Si Gemini no responde, agota cuota, da timeout o no está configurado, CU29
nunca rompe el catálogo: cae a un fallback local (ver
service.py:_interpretar_sin_ia y router.py) que sigue mostrando información
real (promociones vigentes, productos activos) con un mensaje amigable.

Sin tabla propia de conversaciones para este MVP: el historial del chat
vive solo en la sesión del navegador (Angular), y CU29 únicamente recibe las
últimas interacciones que el propio frontend reenvía en cada mensaje (ver
schemas.MensajeAsistenteRequest.historial) para darle contexto a Gemini --
nunca contexto ilimitado.
"""
