// Modelos exclusivos de CU05 — Gestionar usuarios y roles.
// Reutilizan el tipo RolUsuario compartido (usuarios-y-accesos/shared/models);
// no duplican la entidad Usuario, solo agregan los campos que el listado
// administrativo necesita y que CU01 no expone (is_active, created_at).

import { RolUsuario } from '../shared/models/usuario.model';

// Proyección mínima de Ciudad/Sucursal (CU06, P1_SucursalesYCatalogos) que
// necesita el listado/formulario de CU05 — no duplica esos modelos, solo
// refleja lo que la API de CU05 ya expone anidado en cada usuario.
export interface CiudadResumen {
  id: number;
  nombre: string;
}

export interface SucursalResumen {
  id: number;
  nombre: string;
  ciudad: CiudadResumen;
}

// Opciones para los selectores Ciudad → Sucursal de "Nuevo/Editar usuario".
export type CiudadOpcion = CiudadResumen;

export interface SucursalOpcion {
  id: number;
  nombre: string;
}

// Proyección mínima de Proveedor (Gestión de Proveedores, P1_SucursalesYCatalogos).
export interface ProveedorResumen {
  id: number;
  razon_social: string;
}

export type ProveedorOpcion = ProveedorResumen;

export interface UsuarioAdmin {
  id: number;
  nombre: string;
  correo: string;
  rol: RolUsuario;
  is_active: boolean;
  created_at: string;
  sucursal: SucursalResumen | null;
  proveedor: ProveedorResumen | null;
}

// CLIENTE se crea mediante CU02 (registro público) y ADMINISTRADOR GENERAL es
// una cuenta única de sistema: ninguno de los dos se asigna desde CU05.
export type RolAsignableCU05 = Exclude<RolUsuario, 'CLIENTE' | 'ADMINISTRADOR'>;

export interface RolDisponible {
  valor: RolAsignableCU05;
  etiqueta: string;
}

export interface UsuarioCrearPayload {
  nombre: string;
  correo: string;
  password: string;
  rol: RolAsignableCU05;
  sucursal_id?: number | null;
  proveedor_id?: number | null;
}

export interface UsuarioActualizarPayload {
  nombre: string;
  correo: string;
  sucursal_id?: number | null;
  proveedor_id?: number | null;
}

export type CatalogStatusFilter = 'all' | 'active' | 'inactive';

export interface UsuariosListQuery {
  search?: string;
  rol?: RolUsuario;
  estado?: CatalogStatusFilter;
}
