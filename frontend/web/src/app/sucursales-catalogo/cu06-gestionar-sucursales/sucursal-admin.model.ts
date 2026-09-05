// Modelos exclusivos de CU06 — Gestionar sucursales.

export interface Ciudad {
  id: number;
  nombre: string;
  departamento: string;
  is_active: boolean;
}

export interface CiudadCrearPayload {
  nombre: string;
  departamento: string;
  is_active?: boolean;
}

export interface SucursalAdmin {
  id: number;
  nombre: string;
  direccion: string;
  telefono: string;
  is_active: boolean;
  ciudad: Ciudad;
}

export interface SucursalCrearPayload {
  nombre: string;
  ciudad_id: number;
  direccion: string;
  telefono: string;
  is_active?: boolean;
}

export interface SucursalActualizarPayload {
  nombre: string;
  ciudad_id: number;
  direccion: string;
  telefono: string;
}

export type CatalogStatusFilter = 'all' | 'active' | 'inactive';

export interface SucursalesListQuery {
  search?: string;
  ciudad_id?: number;
  estado?: CatalogStatusFilter;
}
