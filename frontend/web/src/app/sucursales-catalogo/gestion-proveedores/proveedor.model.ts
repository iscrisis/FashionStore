// Modelos exclusivos de Gestión de Proveedores. Proveedor NO es Usuario.

export interface Proveedor {
  id: number;
  razon_social: string;
  nombre_contacto: string;
  correo: string;
  telefono: string;
  is_active: boolean;
}

export interface ProveedorPayload {
  razon_social: string;
  nombre_contacto: string;
  correo: string;
  telefono: string;
  is_active?: boolean;
}

export type CatalogStatusFilter = 'all' | 'active' | 'inactive';

export interface ProveedoresListQuery {
  search?: string;
  estado?: CatalogStatusFilter;
}
