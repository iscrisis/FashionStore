// Modelos exclusivos del Panel del Proveedor. El backend siempre resuelve
// "mi proveedor" desde el usuario autenticado — estos modelos nunca incluyen
// un proveedor_id que el cliente pudiera manipular.

export interface MiProveedor {
  id: number;
  razon_social: string;
  nombre_contacto: string;
  correo: string;
  telefono: string;
  is_active: boolean;
}

export interface MiProveedorPayload {
  razon_social: string;
  nombre_contacto: string;
  correo: string;
  telefono: string;
}

// Variantes ya aprobadas (talla+color reales de CU08), agrupadas por color
// para mostrarlas en solo lectura -- el proveedor nunca las elige, las
// decide el Administrador al convertir la propuesta en un Producto.
export interface VariantesPorColor {
  color: string;
  tallas: string[];
}

export type EstadoProductoProveedor = 'PENDIENTE' | 'APROBADO' | 'RECHAZADO';

export interface ProductoProveedor {
  id: number;
  nombre: string;
  descripcion: string | null;
  imagen_url: string | null;
  disponibilidad: boolean;
  is_active: boolean;
  estado: EstadoProductoProveedor;
  variantes: VariantesPorColor[];
}

// Solo lo que el proveedor propone: categoría, temporada, colección, precio,
// tallas y colores son decisiones internas de FashionStore (CU08), no viajan
// aquí.
export interface ProductoProveedorPayload {
  nombre: string;
  descripcion?: string | null;
  disponibilidad?: boolean;
}
