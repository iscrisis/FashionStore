// Modelos exclusivos de CU15 -- Registrar recepción de mercadería. La
// sucursal NUNCA viaja en estos modelos: el backend siempre la resuelve del
// usuario autenticado (ver RegistrarRecepcionPayload más abajo), igual que ya
// hace CU14 (panel-encargado.model.ts) -- este panel solo agrega proveedor +
// variantes recibidas.

export interface ProveedorResumen {
  id: number;
  razon_social: string;
}

export interface TallaResumen {
  id: number;
  nombre: string;
}

export interface ColorResumen {
  id: number;
  nombre: string;
}

export interface VarianteParaRecepcion {
  id: number;
  talla: TallaResumen;
  color: ColorResumen;
}

export interface CategoriaResumen {
  id: number;
  nombre: string;
}

export interface ColeccionResumen {
  id: number;
  nombre: string;
}

export interface ProductoParaRecepcion {
  id: number;
  nombre: string;
  imagen_principal_url: string | null;
  categoria: CategoriaResumen;
  coleccion: ColeccionResumen;
  variantes: VarianteParaRecepcion[];
}

export interface DetalleRecepcionPayload {
  producto_id: number;
  producto_variante_id: number;
  cantidad_recibida: number;
}

export interface RegistrarRecepcionPayload {
  proveedor_id: number;
  observacion?: string | null;
  detalles: DetalleRecepcionPayload[];
}

export interface SucursalResumen {
  id: number;
  nombre: string;
}

export interface UsuarioResumen {
  id: number;
  nombre: string;
}

export interface ProductoResumen {
  id: number;
  nombre: string;
  imagen_principal_url: string | null;
}

export interface DetalleRecepcionOut {
  producto: ProductoResumen;
  variante: VarianteParaRecepcion;
  cantidad_recibida: number;
  stock_resultante: number;
}

export interface RecepcionOut {
  id: number;
  proveedor: ProveedorResumen;
  sucursal: SucursalResumen;
  registrado_por: UsuarioResumen;
  fecha_hora: string;
  observacion: string | null;
  detalles: DetalleRecepcionOut[];
}

// Línea armada en el navegador antes de confirmar -- no es el contrato del
// backend (eso es DetalleRecepcionPayload), es solo el estado del "resumen de
// recepción" que el Encargado va construyendo en pantalla.
export interface LineaResumen {
  productoId: number;
  productoNombre: string;
  varianteId: number;
  tallaNombre: string;
  colorNombre: string;
  cantidad: number;
}
