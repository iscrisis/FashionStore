// Modelo de CU29 -- Obtener recomendaciones mediante IA (Cliente/Invitado).
// Refleja 1:1 la forma que devuelve el backend (ver
// P6_InnovacionYAnalisis/CU29_ObtenerRecomendacionesIA/schemas.py) -- JSON
// puro, preparado para que Flutter lo consuma igual más adelante.
//
// Angular NUNCA llama a Gemini directamente -- solo a
// POST /asistente-ia/mensaje (ver asistente-ia.service.ts). El historial de
// la conversación vive SOLO en memoria de esta sesión del navegador (ver
// asistente-ia.ts) -- se pierde al recargar, es aceptable para este CU.

export type RolMensajeChat = 'usuario' | 'asistente';

export interface TurnoChat {
  rol: RolMensajeChat;
  texto: string;
}

export interface ProductoRecomendado {
  id: number;
  nombre: string;
  imagen_principal_url: string | null;
  // CU32 -- SIEMPRE calculados por FastAPI (precio_efectivo.py), nunca en Angular.
  precio_base: number;
  precio_final: number;
  en_promocion: boolean;
  porcentaje_descuento: number | null;
  // Solo se completan cuando la consulta del Cliente los menciona explícitamente.
  color: string | null;
  talla: string | null;
  disponibilidad_resumen: string | null;
}

export type TipoRespuestaAsistente = 'recomendacion' | 'promocion' | 'disponibilidad' | 'conversacion' | 'fallback';

export interface MensajeAsistenteRequest {
  mensaje: string;
  historial: TurnoChat[];
}

export interface MensajeAsistenteResponse {
  respuesta: string;
  productos: ProductoRecomendado[];
  tipo: TipoRespuestaAsistente;
  hay_mas_resultados: boolean;
}

/** Un mensaje ya renderizado en el chat -- superset de TurnoChat con los
 * productos que trajo esa respuesta del asistente (si los trajo). */
export interface MensajeChat extends TurnoChat {
  productos?: ProductoRecomendado[];
}
