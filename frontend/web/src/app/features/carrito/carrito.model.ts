// Modelo de CU21 -- Usar carrito de compras (Cliente). Refleja 1:1 la forma
// que devuelve el backend (ver P5_ComprasVentasYPagos/CU21_UsarCarritoCompras/
// schemas.py) -- JSON puro, preparado para que Flutter lo consuma igual más
// adelante.
//
// El carrito es SOLO intención de compra digital -- nunca una Reserva
// (crear-reserva.model.ts, CU17), aunque comparta la forma de Producto/
// Variante/Talla/Color. `precio_unitario` es SIEMPRE el precio ACTUAL del
// producto: el backend nunca guarda un precio congelado en el carrito (ver
// Models/carrito.py).
//
// Cada CarritoItemOut es UNA unidad concreta de una variante -- no existe
// `cantidad`: agregar la misma variante otra vez trae OTRO item, con su
// propio item_id y su propio `seleccionado` (checkbox del carrito, para
// marcar qué unidades se consideran en la próxima compra -- no crea Venta
// ni Pago todavía).

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

export interface AgregarItemPayload {
  producto_variante_id: number;
}

export interface ActualizarSeleccionPayload {
  seleccionado: boolean;
}

export interface CarritoItemOut {
  item_id: number;
  producto_variante_id: number;
  producto: ProductoResumen;
  variante: VarianteResumen;
  // `precio_unitario` es SIEMPRE el precio EFECTIVO vigente (CU32 -- con
  // promoción si existe). `precio_base`/`en_promocion`/`porcentaje_descuento`
  // vienen del mismo cálculo, SIEMPRE hecho en FastAPI (ver
  // P6_InnovacionYAnalisis/CU32_GestionarPromociones/precio_efectivo.py).
  precio_unitario: number;
  precio_base: number;
  en_promocion: boolean;
  porcentaje_descuento: number | null;
  seleccionado: boolean;
}

export interface CarritoOut {
  items: CarritoItemOut[];
  subtotal_seleccionado: number;
  fecha_actualizacion: string;
}
