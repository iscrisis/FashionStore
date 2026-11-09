/**
 * Modelo para operación fallida disponible para reintentar.
 */
export interface OperacionFallida {
  uuid: string;
  tipo_operacion: 'VENTA_OFFLINE' | 'RESERVA_OFFLINE';
  estado: 'RECHAZADA' | 'CONFLICTO';
  motivo: string | null;
  numero_intentos: number;
  ultima_fecha_intento: string;
  proximo_reintento_disponible_en_ms: number;
}

/**
 * Resultado de un reintento.
 */
export interface ResultadoReintento {
  uuid_local: string;
  tipo_operacion: 'VENTA_OFFLINE' | 'RESERVA_OFFLINE';
  estado: 'CONFIRMADA' | 'RECHAZADA' | 'CONFLICTO';
  motivo: string | null;
  // Venta
  venta_id?: number | null;
  codigo_venta?: string | null;
  total?: number | null;
  // Reserva
  reserva_id?: number | null;
  codigo_reserva?: string | null;
  // Auditoría
  numero_intento: number;
  proximo_reintento_en_ms: number;
}
