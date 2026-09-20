// Modelo de CU26 -- Registrar devolución o cambio (Cajero). Refleja 1:1 la
// forma que devuelve el backend (ver
// P5_ComprasVentasYPagos/CU26_RegistrarDevolucionCambio/schemas.py) -- JSON
// puro, preparado para que Flutter lo consuma igual más adelante.

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

export interface SucursalResumen {
  id: number;
  nombre: string;
}

export interface DetalleDevolucionOut {
  venta_detalle_id: number;
  producto: ProductoResumen;
  variante: VarianteResumen;
  cantidad_comprada: number;
  cantidad_disponible: number;
  precio_unitario: number;
}

export type TipoVentaDevolucion = 'DIGITAL' | 'PRESENCIAL';
export type MetodoPagoDevolucion = 'STRIPE' | 'EFECTIVO' | 'TARJETA' | 'QR';

export interface VentaDevolucionOut {
  venta_id: number;
  codigo_venta: string;
  fecha_creacion: string;
  sucursal: SucursalResumen;
  cliente_nombre: string | null;
  tipo: TipoVentaDevolucion;
  metodo_pago: MetodoPagoDevolucion;
  total: number;
  detalles: DetalleDevolucionOut[];
}

export type MotivoDevolucion = 'TALLA' | 'DEFECTO' | 'PRODUCTO_INCORRECTO' | 'OTRO';

export interface RegistrarDevolucionPayload {
  venta_id: number;
  venta_detalle_id: number;
  cantidad: number;
  motivo: MotivoDevolucion;
  observacion?: string;
}

export interface DevolucionOut {
  id: number;
  cantidad: number;
  monto_reembolso: number | null;
  metodo_reembolso: string | null;
  estado_reembolso: string | null;
  stripe_refund_id: string | null;
}

export interface VarianteCambioOut {
  producto_variante_id: number;
  talla: TallaResumen;
  color: ColorResumen;
  disponible: number;
}

export interface RegistrarCambioPayload {
  venta_id: number;
  venta_detalle_id: number;
  cantidad: number;
  variante_nueva_id: number;
}

export interface CambioOut {
  id: number;
  cantidad: number;
  variante_original: VarianteResumen;
  variante_nueva: VarianteResumen;
}
