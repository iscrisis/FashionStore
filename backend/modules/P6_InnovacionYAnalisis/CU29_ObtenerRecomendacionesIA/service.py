"""Reglas de negocio de CU29 -- Obtener recomendaciones mediante IA.

Flujo, siempre en este orden (nunca al revés -- ver __init__.py):

  1. INTERPRETAR -- se le pide a Gemini que devuelva SOLO un JSON con la
     intención y los criterios mencionados (categoría/color/talla/colección/
     ciudad/presupuesto). Si Gemini no está disponible (sin configurar,
     timeout, cuota, 5xx...), se interpreta con un resolver local simple sin
     IA (_interpretar_sin_ia): nunca se deja de responder por esto.
  2. CONSULTAR -- con esos criterios ya extraídos, FastAPI busca productos
     REALES en PostgreSQL a través de CatalogoPublicoRepository (CU11) y
     calcula su precio con precio_efectivo.py (CU32) -- Gemini nunca toca la
     base de datos.
  3. REDACTAR -- con, como máximo, los 3 productos que se van a mostrar,
     FastAPI arma un "contexto comercial" de texto (solo con datos ya
     verificados) y le pide a Gemini que redacte la respuesta en lenguaje
     natural. Si esta segunda llamada falla, se usa una redacción propia por
     plantilla -- los productos encontrados nunca se pierden por esto.

El array `productos` de la respuesta SIEMPRE sale del paso 2 (esta misma
consulta a PostgreSQL) -- Gemini jamás decide qué productos se devuelven,
solo cómo se describen. No hace falta "verificar que los ids existan": por
construcción, nunca se arma un ProductoRecomendadoOut a partir de otra cosa
que no sea una fila de Producto ya leída en este mismo request.

Cliente autenticado (opcional, ver app.core.deps.get_current_usuario_opcional
y router.py): se arma un resumen mínimo de preferencias a partir de sus
compras PAGADAS reales (mismo Venta/VentaDetalle que CU27) -- categorías/
talla/colores/colección más frecuentes. Nunca se envía a Gemini correo,
teléfono, contraseña, JWT ni nombre completo -- ver _resumen_preferencias.
Sin historial (Cliente nuevo) o sin sesión (Invitado): el asistente sigue
funcionando con recomendaciones generales (catálogo activo/promociones),
nunca con un mensaje de error.
"""

import re
from collections import Counter
from decimal import Decimal

from sqlalchemy.orm import Session

from modules.P1_SucursalesYCatalogos.CU11_ConsultarCatalogoPrendas.repository import (
    CatalogoPublicoRepository,
)
from modules.P1_SucursalesYCatalogos.Models.producto import Producto
from modules.P2_UsuariosYAccesos.Models.rol import RolUsuario
from modules.P2_UsuariosYAccesos.Models.usuario import Usuario
from modules.P6_InnovacionYAnalisis.CU32_GestionarPromociones.precio_efectivo import (
    PrecioEfectivo,
    obtener_precios_efectivos,
)

from . import gemini_client
from .gemini_client import GeminiNoDisponibleError
from .repository import (
    CatalogoResolverRepository,
    DisponibilidadResumenRepository,
    PreferenciasClienteRepository,
)
from .schemas import MensajeAsistenteRequest, ProductoRecomendadoOut

_MAX_PRODUCTOS_RESPUESTA = 3
_MAX_CANDIDATOS = 12
_MAX_TURNOS_HISTORIAL = 6

_INTENCION_A_TIPO = {
    "busqueda_producto": "recomendacion",
    "recomendacion_personal": "recomendacion",
    "promociones": "promocion",
    "disponibilidad": "disponibilidad",
    "conversacion": "conversacion",
}

_MENSAJE_IA_NO_DISPONIBLE = (
    "El asistente no está disponible en este momento. Puedes seguir explorando nuestro catálogo."
)


class AsistenteIAService:
    def __init__(self, db: Session):
        self._db = db
        self._catalogo = CatalogoPublicoRepository(db)
        self._resolver = CatalogoResolverRepository(db)
        self._disponibilidad = DisponibilidadResumenRepository(db)
        self._preferencias_repo = PreferenciasClienteRepository(db)

    def responder(self, payload: MensajeAsistenteRequest, cliente: Usuario | None) -> dict:
        mensaje = payload.mensaje.strip()
        historial = [turno.model_dump() for turno in payload.historial[-_MAX_TURNOS_HISTORIAL:]]

        es_cliente = cliente is not None and cliente.rol == RolUsuario.CLIENTE
        preferencias = self._resumen_preferencias(cliente) if es_cliente else None

        try:
            filtros = gemini_client.interpretar_consulta(mensaje, historial)
            interpretado_con_ia = True
        except GeminiNoDisponibleError:
            filtros = self._interpretar_sin_ia(mensaje)
            interpretado_con_ia = False

        intencion = filtros.get("intencion")
        if intencion not in _INTENCION_A_TIPO:
            intencion = "busqueda_producto"

        productos_orm, hay_mas = self._buscar_productos(filtros, intencion, preferencias)
        top = productos_orm[:_MAX_PRODUCTOS_RESPUESTA]
        precios = obtener_precios_efectivos(self._db, top) if top else {}
        productos_salida = [self._a_producto_salida(p, precios[p.id], filtros) for p in top]

        contexto = self._construir_contexto(productos_salida, hay_mas, preferencias)

        respuesta_texto = None
        if interpretado_con_ia:
            try:
                respuesta_texto = gemini_client.generar_respuesta(mensaje, historial, contexto)
            except GeminiNoDisponibleError:
                respuesta_texto = None

        if respuesta_texto is None:
            respuesta_texto = self._respuesta_plantilla(productos_salida, hay_mas, interpretado_con_ia)

        return {
            "respuesta": respuesta_texto,
            "productos": productos_salida,
            "tipo": _INTENCION_A_TIPO[intencion] if interpretado_con_ia else "fallback",
            "hay_mas_resultados": hay_mas,
        }

    # ------------------------------------------------------------------
    # Interpretación sin IA (Gemini no disponible) -- coincidencia simple de
    # los nombres YA activos del catálogo dentro del mensaje, sin inventar
    # nada que no exista en la base de datos.
    # ------------------------------------------------------------------
    def _interpretar_sin_ia(self, mensaje: str) -> dict:
        texto = mensaje.lower()
        categoria = self._buscar_nombre_en_texto(texto, self._resolver.categorias_activas())
        color = self._buscar_nombre_en_texto(texto, self._resolver.colores_activos())
        talla = self._buscar_nombre_en_texto(texto, self._resolver.tallas_activas())
        coleccion = self._buscar_nombre_en_texto(texto, self._resolver.colecciones_activas())

        intencion = "busqueda_producto"
        if any(palabra in texto for palabra in ("promo", "descuento", "oferta", "rebaja")):
            intencion = "promociones"
        elif any(palabra in texto for palabra in ("disponib", "dónde", "donde", "sucursal")):
            intencion = "disponibilidad"
        elif any(palabra in texto for palabra in ("recomien", "recomend", "sugiere", "sugerencia")):
            intencion = "recomendacion_personal"

        # Sin categoría/color/talla/colección reconocidos, el mensaje puede
        # seguir mencionando un nombre de prenda que SÍ existe en el
        # catálogo (ej. "chaquetas", "poleras") -- sin esto, el fallback sin
        # IA nunca intentaría buscar por nombre y siempre caería al catálogo
        # genérico. Nunca se combina con un filtro estructurado ya
        # encontrado, para no sobre-restringir la búsqueda.
        texto_busqueda = None
        if not any([categoria, color, talla, coleccion]):
            texto_busqueda = self._palabra_clave_heuristica(mensaje)

        return {
            "intencion": intencion,
            "categoria": categoria,
            "color": color,
            "talla": talla,
            "coleccion": coleccion,
            "ciudad": None,
            "texto_busqueda": texto_busqueda,
            "presupuesto_max": None,
        }

    _STOPWORDS_ES = {
        "quiero", "quisiera", "busco", "buscando", "necesito", "tienen", "tienes",
        "tengo", "hay", "algo", "alguna", "algun", "alguno", "de", "del", "una",
        "un", "unos", "unas", "el", "la", "los", "las", "me", "mi", "mis", "que",
        "por", "para", "con", "en", "y", "o", "es", "son", "esta", "está",
        "estan", "están", "recomienda", "recomiendas", "recomiendame",
        "recomiéndame", "sugiereme", "sugiéreme", "porfa", "porfavor", "favor",
        "hola", "gracias", "cual", "cuales", "cuál", "cuáles", "donde", "dónde",
        "como", "cómo", "tiene", "tienda", "fashionstore", "prenda", "prendas",
        "producto", "productos", "algo", "parecido", "parecida",
    }

    @classmethod
    def _palabra_clave_heuristica(cls, mensaje: str) -> str | None:
        """Palabra de contenido más larga del mensaje, descartando conectores
        y verbos comunes -- una aproximación simple (sin NLP) para intentar
        una búsqueda por nombre real cuando no hay IA disponible."""
        palabras = re.findall(r"[a-záéíóúñ]+", mensaje.lower())
        candidatas = [p for p in palabras if len(p) >= 3 and p not in cls._STOPWORDS_ES]
        if not candidatas:
            return None
        return max(candidatas, key=len)

    @staticmethod
    def _variantes_busqueda(texto: str) -> list[str]:
        """Normalización mínima de plural -> singular en español (ej.
        "chaquetas" también prueba "chaqueta", "pantalones" también prueba
        "pantalon") -- reglas simples, sin librería de NLP, suficientes para
        los casos reales de nombres de prendas del catálogo."""
        variantes = [texto]
        minuscula = texto.strip().lower()
        if len(minuscula) > 4 and minuscula.endswith("es"):
            variantes.append(minuscula[:-2])
        if len(minuscula) > 3 and minuscula.endswith("s"):
            candidato = minuscula[:-1]
            if candidato not in variantes:
                variantes.append(candidato)
        return variantes

    @staticmethod
    def _raiz_comparable(palabra: str) -> str:
        """Raíz simple para tolerar género/número básico del español (ej.
        "blancas" ~ "blanco", "negra" ~ "negro") -- solo para palabras de 4+
        letras, para no convertir una talla corta como "S"/"M" en un patrón
        demasiado laxo (ver _buscar_nombre_en_texto, que compara palabras
        completas ya tokenizadas, nunca substrings)."""
        p = palabra.lower()
        if len(p) >= 5 and p.endswith(("as", "os")):
            return p[:-2]
        if len(p) >= 4 and p.endswith(("a", "o", "s", "e")):
            return p[:-1]
        return p

    @classmethod
    def _buscar_nombre_en_texto(cls, texto: str, opciones: list) -> str | None:
        """Compara la RAÍZ de cada palabra del mensaje (tokenizada, nunca un
        substring plano -- ver _raiz_comparable) contra la raíz de cada
        nombre del catálogo. Tolera género/número básico ("blancas"
        encuentra el color "Blanco") sin el falso positivo de un simple
        `in` (una talla "S" ya no aparece dentro de "busco", porque se
        comparan palabras completas)."""
        palabras_mensaje = {cls._raiz_comparable(p) for p in re.findall(r"[a-záéíóúñ]+", texto)}
        for opcion in opciones:
            if cls._raiz_comparable(opcion.nombre) in palabras_mensaje:
                return opcion.nombre
        return None

    # ------------------------------------------------------------------
    # Búsqueda real en PostgreSQL -- únicamente vía CatalogoPublicoRepository
    # (CU11), con un ensanche progresivo de filtros si la combinación exacta
    # no encuentra nada (nunca inventa productos, solo relaja criterios).
    # ------------------------------------------------------------------
    def _buscar_productos(
        self, filtros: dict, intencion: str, preferencias: dict | None
    ) -> tuple[list[Producto], bool]:
        categoria_cruda = filtros.get("categoria")
        coleccion_cruda = filtros.get("coleccion")
        categoria_id = self._resolver.resolver_categoria_id(categoria_cruda)
        color_id = self._resolver.resolver_color_id(filtros.get("color"))
        talla_id = self._resolver.resolver_talla_id(filtros.get("talla"))
        coleccion_id = self._resolver.resolver_coleccion_id(coleccion_cruda)
        texto = filtros.get("texto_busqueda")
        texto = texto.strip() if isinstance(texto, str) and texto.strip() else None

        # Gemini (o el resolver local) puede mencionar una categoría/
        # colección que NO existe tal cual en el catálogo real (ej. el
        # Cliente dice "chaquetas" pero esos productos están categorizados
        # como "Poleras" -- no existe una categoría "Chaquetas"). En vez de
        # descartar ese valor sin más, se reutiliza como término de búsqueda
        # por NOMBRE -- sigue siendo una palabra real que el Cliente
        # mencionó, y puede coincidir con el nombre del producto aunque no
        # con ninguna categoría/colección registrada.
        if texto is None:
            for crudo, resuelto in ((categoria_cruda, categoria_id), (coleccion_cruda, coleccion_id)):
                if isinstance(crudo, str) and crudo.strip() and resuelto is None:
                    texto = crudo.strip()
                    break

        sin_criterios = not any([categoria_id, color_id, talla_id, coleccion_id, texto])
        if intencion == "recomendacion_personal" and sin_criterios and preferencias:
            categoria_id = preferencias.get("categoria_id")
            coleccion_id = preferencias.get("coleccion_id")

        habia_criterios = any([categoria_id, color_id, talla_id, coleccion_id, texto])
        # search (CatalogoPublicoRepository, CU11) busca el término como
        # substring EXACTO del nombre -- un plural escrito tal cual
        # ("chaquetas") nunca encuentra un producto guardado en singular
        # ("Chaqueta"), porque el término buscado sería más largo que el
        # nombre real. Se prueban varias formas del término (nunca solo la
        # literal) antes de rendirse.
        terminos = self._variantes_busqueda(texto) if texto else [None]

        combos = [
            {"categoria_id": categoria_id, "coleccion_id": coleccion_id, "talla_id": talla_id, "color_id": color_id},
            {"categoria_id": categoria_id, "coleccion_id": coleccion_id, "talla_id": None, "color_id": color_id},
            {"categoria_id": categoria_id, "coleccion_id": coleccion_id, "talla_id": None, "color_id": None},
            {"categoria_id": categoria_id, "coleccion_id": None, "talla_id": None, "color_id": None},
        ]

        productos: list[Producto] = []
        for termino in terminos:
            for combo in combos:
                candidatos = self._catalogo.listar_productos(search=termino, **combo)
                if candidatos:
                    productos = candidatos
                    break
            if productos:
                break

        if not productos and habia_criterios:
            # Ninguna combinación de filtros dio resultado -- último intento
            # real antes de rendirse: solo el término de búsqueda (o alguna
            # de sus variantes), sin ningún otro filtro que lo restrinja.
            for termino in terminos:
                if termino is None:
                    continue
                candidatos = self._catalogo.listar_productos(search=termino)
                if candidatos:
                    productos = candidatos
                    break

        if not productos:
            # Última red de seguridad -- catálogo activo general (nunca
            # vacío mientras haya productos), para no dejar al Cliente sin
            # ninguna sugerencia real.
            productos = self._catalogo.listar_productos()

        presupuesto = filtros.get("presupuesto_max")
        if isinstance(presupuesto, (int, float)) and presupuesto > 0 and productos:
            precios = obtener_precios_efectivos(self._db, productos)
            productos = [p for p in productos if precios[p.id].precio_final <= Decimal(str(presupuesto))]

        if (intencion == "promociones" or filtros.get("solo_promocion")) and productos:
            precios = obtener_precios_efectivos(self._db, productos)
            en_promocion = [p for p in productos if precios[p.id].en_promocion]
            if en_promocion:
                productos = en_promocion

        productos = productos[:_MAX_CANDIDATOS]
        hay_mas = len(productos) > _MAX_PRODUCTOS_RESPUESTA
        return productos, hay_mas

    # ------------------------------------------------------------------
    # Preferencias del Cliente autenticado -- solo categorías/talla/colores/
    # colección más frecuentes de sus compras PAGADAS reales. Nunca datos
    # personales (ver docstring del módulo).
    # ------------------------------------------------------------------
    def _resumen_preferencias(self, cliente: Usuario) -> dict | None:
        detalles = self._preferencias_repo.compras_recientes(cliente.id)
        if not detalles:
            return None

        producto_ids = {detalle.producto_variante.producto_id for detalle in detalles}
        productos = self._preferencias_repo.productos_por_ids(producto_ids)

        categorias: Counter[str] = Counter()
        colecciones: Counter[str] = Counter()
        tallas: Counter[str] = Counter()
        colores: Counter[str] = Counter()
        for detalle in detalles:
            producto = productos.get(detalle.producto_variante.producto_id)
            if producto is not None:
                categorias[producto.categoria.nombre] += 1
                colecciones[producto.coleccion.nombre] += 1
            tallas[detalle.producto_variante.talla.nombre] += 1
            colores[detalle.producto_variante.color.nombre] += 1

        if not categorias and not tallas and not colores:
            return None

        categoria_top = categorias.most_common(1)[0][0] if categorias else None
        coleccion_top = colecciones.most_common(1)[0][0] if colecciones else None

        lineas = ["Preferencias del cliente (según su historial real de compras):"]
        if categorias:
            lineas.append(f"- categorías frecuentes: {', '.join(n for n, _ in categorias.most_common(3))}")
        if tallas:
            lineas.append(f"- talla frecuente: {tallas.most_common(1)[0][0]}")
        if colores:
            lineas.append(f"- colores frecuentes: {', '.join(n for n, _ in colores.most_common(3))}")
        if colecciones:
            lineas.append(f"- colección frecuente: {coleccion_top}")

        return {
            "categoria_id": self._resolver.resolver_categoria_id(categoria_top),
            "coleccion_id": self._resolver.resolver_coleccion_id(coleccion_top),
            "texto": "\n".join(lineas),
        }

    # ------------------------------------------------------------------
    # Armado de salida -- SIEMPRE a partir de una fila de Producto ya leída
    # de PostgreSQL en este mismo request, nunca de algo que Gemini sugirió.
    # ------------------------------------------------------------------
    def _a_producto_salida(
        self, producto: Producto, precio: PrecioEfectivo, filtros: dict
    ) -> ProductoRecomendadoOut:
        ciudad_id = self._resolver.resolver_ciudad_id(filtros.get("ciudad"))
        nombres, total = self._disponibilidad.sucursales_con_stock(producto.id, ciudad_id)
        if not nombres:
            resumen = "Sin stock disponible por el momento."
        elif total > len(nombres):
            resumen = f"Disponible en {', '.join(nombres)} y {total - len(nombres)} sucursal(es) más."
        else:
            resumen = f"Disponible en {', '.join(nombres)}."

        color_pedido = (filtros.get("color") or "").strip().lower()
        color = next((c.nombre for c in producto.colores if c.nombre.lower() == color_pedido), None)
        talla_pedida = (filtros.get("talla") or "").strip().lower()
        talla = next((t.nombre for t in producto.tallas if t.nombre.lower() == talla_pedida), None)

        return ProductoRecomendadoOut(
            id=producto.id,
            nombre=producto.nombre,
            imagen_principal_url=producto.imagen_principal_url,
            precio_base=float(precio.precio_base),
            precio_final=float(precio.precio_final),
            en_promocion=precio.en_promocion,
            porcentaje_descuento=float(precio.porcentaje_descuento) if precio.porcentaje_descuento is not None else None,
            color=color,
            talla=talla,
            disponibilidad_resumen=resumen,
        )

    # ------------------------------------------------------------------
    # Contexto comercial para Gemini (paso 3) y plantilla de respaldo si esa
    # llamada falla -- ambos usan ÚNICAMENTE los productos ya resueltos.
    # ------------------------------------------------------------------
    @staticmethod
    def _construir_contexto(
        productos: list[ProductoRecomendadoOut], hay_mas: bool, preferencias: dict | None
    ) -> str:
        if not productos:
            bloque = "No se encontraron productos que coincidan con la consulta en el catálogo actual."
        else:
            lineas = ["Productos encontrados:"]
            for producto in productos:
                linea = f"- ID {producto.id} -- {producto.nombre}"
                if producto.color:
                    linea += f", color {producto.color}"
                if producto.talla:
                    linea += f", talla {producto.talla}"
                if producto.en_promocion:
                    linea += (
                        f" -- antes Bs {producto.precio_base:.2f}, ahora Bs {producto.precio_final:.2f} "
                        f"({producto.porcentaje_descuento:.0f}% de descuento)"
                    )
                else:
                    linea += f" -- Bs {producto.precio_final:.2f}"
                linea += f". {producto.disponibilidad_resumen}"
                lineas.append(linea)
            bloque = "\n".join(lineas)
            if hay_mas:
                bloque += "\nHay más opciones similares disponibles en el catálogo, además de estas."

        if preferencias:
            bloque += f"\n\n{preferencias['texto']}"
        return bloque

    @staticmethod
    def _respuesta_plantilla(
        productos: list[ProductoRecomendadoOut], hay_mas: bool, interpretado_con_ia: bool
    ) -> str:
        prefijo = "" if interpretado_con_ia else f"{_MENSAJE_IA_NO_DISPONIBLE} "
        if not productos:
            return f"{prefijo}No encontré productos exactos para tu búsqueda, pero puedes seguir explorando nuestro catálogo.".strip()
        nombres = ", ".join(producto.nombre for producto in productos)
        extra = " Encontré más opciones en el catálogo." if hay_mas else ""
        return f"{prefijo}Estas son algunas opciones que encontré: {nombres}.{extra}".strip()
