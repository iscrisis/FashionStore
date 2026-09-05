// Modelos exclusivos de CU08 -- Gestionar productos. Reutiliza los catálogos
// de Proveedores, CU09 (categorías/tallas/colores) y CU10 (temporadas/
// colecciones) -- no los duplica.

export interface ProveedorResumen {
  id: number;
  razon_social: string;
}

export interface CategoriaResumen {
  id: number;
  nombre: string;
}

export interface TemporadaResumen {
  id: number;
  nombre: string;
}

export interface ColeccionResumen {
  id: number;
  nombre: string;
}

export interface TallaResumen {
  id: number;
  nombre: string;
}

export interface ColorResumen {
  id: number;
  nombre: string;
}

export interface ProductoImagen {
  id: number;
  url: string;
  orden: number;
}

export interface ProductoVariante {
  id: number;
  talla: TallaResumen;
  color: ColorResumen;
  is_active: boolean;
}

export interface Producto {
  id: number;
  nombre: string;
  descripcion: string | null;
  precio_venta: string;
  is_active: boolean;
  proveedor: ProveedorResumen;
  producto_proveedor_id: number | null;
  categoria: CategoriaResumen;
  temporada: TemporadaResumen;
  coleccion: ColeccionResumen;
  tallas: TallaResumen[];
  colores: ColorResumen[];
  variantes: ProductoVariante[];
  imagen_principal_url: string | null;
  imagenes: ProductoImagen[];
}

export interface ProductoPayload {
  nombre: string;
  descripcion?: string | null;
  proveedor_id: number;
  producto_proveedor_id?: number | null;
  categoria_id: number;
  temporada_id: number;
  coleccion_id: number;
  precio_venta: string;
  talla_ids: number[];
  color_ids: number[];
  is_active?: boolean;
}

export interface PropuestaProveedor {
  id: number;
  nombre: string;
  descripcion: string | null;
  disponibilidad: boolean;
  proveedor: ProveedorResumen;
  temporada: TemporadaResumen;
  coleccion: ColeccionResumen;
}

export type CatalogStatusFilter = 'all' | 'active' | 'inactive';

export interface ProductosListQuery {
  search?: string;
  categoria_id?: number;
  temporada_id?: number;
  coleccion_id?: number;
  proveedor_id?: number;
  estado?: CatalogStatusFilter;
}
