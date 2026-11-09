/**CU12 — Modelo de resultado de sincronización.*/

export type TipoOperacion = 'VENTA_OFFLINE' | 'RESERVA_OFFLINE';
export type EstadoResultado = 'CONFIRMADA' | 'RECHAZADA' | 'CONFLICTO';

export interface ResultadoSincronizacion {
  uuid_local: string;
  tipo_operacion: TipoOperacion;
  estado: EstadoResultado;
  motivo: string | null;

  // Identificadores oficiales
  venta_id: number | null;
  reserva_id: number | null;
  codigo_venta: string | null;
  codigo_reserva: string | null;

  // Temporales
  fecha_local: Date;
  fecha_sincronizacion: Date | null;

  // Negocio
  total: number | null;
  empresa_id: number;
  sucursal_id: number;
}

export interface ResumenResultados {
  confirmadas: number;
  pendientes: number;
  rechazadas: number;
  conflictos: number;
  total: number;
}
