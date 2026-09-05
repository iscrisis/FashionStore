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

export interface TemporadaResumen {
  id: number;
  nombre: string;
}

export interface ColeccionResumen {
  id: number;
  nombre: string;
}

export interface ProductoProveedor {
  id: number;
  nombre: string;
  descripcion: string | null;
  disponibilidad: boolean;
  is_active: boolean;
  temporada: TemporadaResumen;
  coleccion: ColeccionResumen;
}

export interface ProductoProveedorPayload {
  nombre: string;
  descripcion?: string | null;
  temporada_id: number;
  coleccion_id: number;
  disponibilidad?: boolean;
}
