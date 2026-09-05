// Modelos del catálogo público (CU11) -- solo lectura, sin autenticación.
// Reutiliza los mismos datos administrados por CU08 (productos), CU09
// (categorías/tallas/colores) y CU10 (temporadas/colecciones); no los duplica.

export interface CategoriaPublica {
  id: number;
  nombre: string;
  imagen_url: string | null;
}

export interface TemporadaPublica {
  id: number;
  nombre: string;
}

export interface ColeccionPublica {
  id: number;
  nombre: string;
  descripcion: string | null;
  temporada: TemporadaPublica;
}

export interface TallaPublica {
  id: number;
  nombre: string;
}

export interface ColorPublico {
  id: number;
  nombre: string;
}

export interface ProductoImagenPublica {
  id: number;
  url: string;
  orden: number;
}

export interface ProductoPublico {
  id: number;
  nombre: string;
  descripcion: string | null;
  precio_venta: number;
  imagen_principal_url: string | null;
  imagenes: ProductoImagenPublica[];
  categoria: CategoriaPublica;
  temporada: TemporadaPublica;
  coleccion: ColeccionPublica;
  tallas: TallaPublica[];
  colores: ColorPublico[];
}

export interface CatalogoProductosQuery {
  search?: string;
  categoria_id?: number;
  coleccion_id?: number;
  talla_id?: number;
  color_id?: number;
}
