// Modelo de CU23 -- Procesar pago electrónico (Cliente). Refleja 1:1 la
// forma que devuelve el backend (ver
// P5_ComprasVentasYPagos/CU23_ProcesarPagoElectronico/schemas.py) -- JSON
// puro, preparado para que Flutter lo consuma igual más adelante: Angular
// solo pide la Checkout Session, redirige a la URL de Stripe y luego pide
// la verificación -- nunca decide por sí solo que un pago se completó.

export interface CrearCheckoutPayload {
  venta_id: number;
}

export interface CheckoutSessionOut {
  checkout_url: string;
}

export interface VerificarPagoPayload {
  session_id: string;
}

export interface SucursalVentaOut {
  id: number;
  nombre: string;
  direccion: string;
  ciudad: string;
}

export interface VentaPagadaOut {
  id: number;
  codigo_venta: string;
  estado: string;
  total: number;
  sucursal: SucursalVentaOut;
}
