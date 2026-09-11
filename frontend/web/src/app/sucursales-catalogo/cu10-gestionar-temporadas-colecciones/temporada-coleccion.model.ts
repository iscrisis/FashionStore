// Modelos exclusivos de CU10 — Gestionar temporadas y colecciones.

export interface Temporada {
  id: number;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  is_active: boolean;
}

export interface TemporadaPayload {
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  is_active?: boolean;
}

export interface Coleccion {
  id: number;
  nombre: string;
  descripcion: string | null;
  is_active: boolean;
  es_destacada_inicio: boolean;
  imagen_destacada_url: string | null;
  temporada: Temporada;
}

export interface ColeccionPayload {
  nombre: string;
  temporada_id: number;
  descripcion?: string | null;
  is_active?: boolean;
}

export type CatalogStatusFilter = 'all' | 'active' | 'inactive';

export interface TemporadasListQuery {
  search?: string;
  estado?: CatalogStatusFilter;
}

export interface ColeccionesListQuery {
  search?: string;
  temporada_id?: number;
  estado?: CatalogStatusFilter;
}
