// Modelo de CU27 -- Consultar historial de compras. Refleja 1:1 la forma
// que devuelve el backend (ver
// P5_ComprasVentasYPagos/CU27_ConsultarHistorialCompras/schemas.py) -- JSON
// puro, preparado para que Flutter lo consuma igual más adelante.
//
// Compartido entre features/cliente/historial-compras (Cliente) y
// features/cajero/historial (Cajero) -- el backend ya resuelve, según el
// rol del actor autenticado, qué ventas puede ver cada uno; este modelo es
// el mismo para ambos, nunca duplicado.

export interface SucursalHistorialOut {
  id: number;
  nombre: string;
  ciudad: string;
}

export type TipoVentaHistorial = 'DIGITAL' | 'PRESENCIAL';
export type MetodoPagoHistorial = 'STRIPE' | 'EFECTIVO' | 'TARJETA' | 'QR';

export interface VentaHistorialOut {
  venta_id: number;
  codigo_venta: string;
  fecha: string;
  sucursal: SucursalHistorialOut;
  cliente_nombre: string | null;
  tipo: TipoVentaHistorial;
  metodo_pago: MetodoPagoHistorial;
  total: number;
  // CU26 (solo lectura, nunca se recalcula aquí): si esta Venta ya tiene
  // una devolución/cambio registrado, y el mensaje discreto ya armado por
  // el backend para mostrar debajo del código (nunca varios badges, ver
  // CU27_ConsultarHistorialCompras/service.py: _leyenda_postventa).
  tiene_postventa: boolean;
  leyenda_postventa: string | null;
}

export interface FiltroHistorial {
  desde?: string;
  hasta?: string;
  codigo_venta?: string;
}
