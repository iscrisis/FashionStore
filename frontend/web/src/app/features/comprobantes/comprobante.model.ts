// Modelo de CU31 -- Emitir comprobante de venta. Refleja 1:1 la forma que
// devuelve el backend (ver
// P5_ComprasVentasYPagos/CU31_EmitirComprobanteVenta/schemas.py) -- JSON
// puro, preparado para que Flutter lo consuma igual más adelante.
//
// Compartido entre features/cliente/comprobantes (Cliente) y
// features/cajero/comprobantes (Cajero) -- el backend ya resuelve, según el
// rol del actor autenticado, si puede ver ESTE comprobante o no; este modelo
// es el mismo para ambos, nunca duplicado.

export interface TallaResumen {
  id: number;
  nombre: string;
}

export interface ColorResumen {
  id: number;
  nombre: string;
}

export interface VarianteResumen {
  id: number;
  talla: TallaResumen;
  color: ColorResumen;
}

export interface ProductoResumen {
  id: number;
  nombre: string;
  imagen_principal_url: string | null;
}

export interface SucursalComprobanteOut {
  id: number;
  nombre: string;
  direccion: string;
  ciudad: string;
}

export interface ClienteComprobanteOut {
  nombre: string;
  correo: string;
}

export interface DetalleComprobanteOut {
  producto: ProductoResumen;
  variante: VarianteResumen;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

export type TipoVentaComprobante = 'DIGITAL' | 'PRESENCIAL';
export type MetodoPagoComprobante = 'STRIPE' | 'EFECTIVO' | 'TARJETA' | 'QR';

export interface ComprobanteVentaOut {
  venta_id: number;
  codigo_venta: string;
  fecha_creacion: string;
  tipo: TipoVentaComprobante;
  sucursal: SucursalComprobanteOut;
  cliente: ClienteComprobanteOut | null;
  detalles: DetalleComprobanteOut[];
  total: number;
  metodo_pago: MetodoPagoComprobante;
  estado: string;
  estado_pago: string;
}

export interface EnviarComprobanteOut {
  enviado: boolean;
  mensaje: string;
}
