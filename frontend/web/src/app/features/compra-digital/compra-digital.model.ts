// Modelo de CU22 -- Realizar compra digital (Cliente). Refleja 1:1 la forma
// que devuelve el backend (ver P5_ComprasVentasYPagos/CU22_RealizarCompraDigital/
// schemas.py) -- JSON puro, preparado para que Flutter lo consuma igual más
// adelante.
//
// Reutiliza la forma de Producto/Variante/Talla/Color de carrito.model.ts
// (CU21) -- los items de la compra son EXACTAMENTE los que el Cliente ya
// seleccionó en su carrito, nunca una lista nueva que arme Angular.

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

export interface LineaCompraOut {
  item_id: number;
  producto_variante_id: number;
  producto: ProductoResumen;
  variante: VarianteResumen;
  // CU32 -- `precio_unitario` es SIEMPRE el precio EFECTIVO vigente (con
  // promoción si existe); `precio_base`/`en_promocion`/`porcentaje_descuento`
  // vienen del mismo cálculo en FastAPI.
  precio_unitario: number;
  precio_base: number;
  en_promocion: boolean;
  porcentaje_descuento: number | null;
}

export interface ResumenCompraOut {
  items: LineaCompraOut[];
  total: number;
}

export interface SucursalCompraOut {
  id: number;
  nombre: string;
  direccion: string;
  disponible_para_compra: boolean;
}

export interface ConfirmarCompraPayload {
  sucursal_id: number;
}

export interface SucursalVentaOut {
  id: number;
  nombre: string;
  direccion: string;
  ciudad: string;
}

export interface VentaDetalleOut {
  producto: ProductoResumen;
  variante: VarianteResumen;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

export interface VentaOut {
  id: number;
  codigo_venta: string;
  sucursal: SucursalVentaOut;
  tipo: string;
  estado: string;
  total: number;
  fecha_creacion: string;
  detalles: VentaDetalleOut[];
}
