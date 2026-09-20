// Modelo de CU24 -- Registrar venta presencial (Cajero). Refleja 1:1 la
// forma que devuelve el backend (ver
// P5_ComprasVentasYPagos/CU24_RegistrarVentaPresencial/schemas.py) -- JSON
// puro, preparado para que Flutter lo consuma igual más adelante.
//
// Reutiliza el modelo Venta/VentaDetalle que ya creó CU22 (compra digital) y
// CU23 (pago electrónico) -- no es un sistema de ventas paralelo, solo un
// tipo/origen distinto sobre la misma entidad.

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

export interface ProductoBusquedaOut {
  producto_variante_id: number;
  producto: ProductoResumen;
  variante: VarianteResumen;
  // CU32 -- `precio_unitario` es SIEMPRE el precio EFECTIVO vigente (el
  // mismo que ve el Cliente en la Web, con promoción si existe) --
  // calculado en FastAPI, nunca en Angular.
  precio_unitario: number;
  en_promocion: boolean;
  porcentaje_descuento: number | null;
  disponible: number;
}

export interface ItemVentaDirecta {
  producto_variante_id: number;
  cantidad: number;
}

export interface CrearVentaDirectaPayload {
  items: ItemVentaDirecta[];
}

export interface VentaDetalleOut {
  producto: ProductoResumen;
  variante: VarianteResumen;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

export interface ReservaResumenOut {
  codigo_reserva: string;
  cliente_nombre: string;
}

export interface VentaPresencialOut {
  id: number;
  codigo_venta: string;
  tipo: string;
  estado: string;
  origen: string;
  total: number;
  fecha_creacion: string;
  reserva: ReservaResumenOut | null;
  detalles: VentaDetalleOut[];
}

// CU25 -- Procesar pago presencial. Misma Venta que arma CU24 -- confirmar
// el pago es un paso sobre ella, no un recurso aparte (ver
// P5_ComprasVentasYPagos/CU25_ProcesarPagoPresencial/schemas.py).

export type MetodoPago = 'EFECTIVO' | 'TARJETA' | 'QR';
export type TipoTarjeta = 'DEBITO' | 'CREDITO';

export interface ConfirmarPagoEfectivoPayload {
  metodo_pago: 'EFECTIVO';
  monto_recibido: number;
}

export interface ConfirmarPagoTarjetaPayload {
  metodo_pago: 'TARJETA';
  tipo_tarjeta: TipoTarjeta;
  referencia?: string;
}

export interface ConfirmarPagoQrPayload {
  metodo_pago: 'QR';
  referencia?: string;
}

export type ConfirmarPagoPayload =
  | ConfirmarPagoEfectivoPayload
  | ConfirmarPagoTarjetaPayload
  | ConfirmarPagoQrPayload;

export interface PagoConfirmadoOut {
  codigo_venta: string;
  total: number;
  metodo_pago: string;
  monto_recibido: number | null;
  cambio: number | null;
}
