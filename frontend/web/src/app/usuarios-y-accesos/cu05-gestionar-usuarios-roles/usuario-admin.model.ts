// Modelos exclusivos de CU05 — Gestionar usuarios y roles.
// Reutilizan el tipo RolUsuario compartido (usuarios-y-accesos/shared/models);
// no duplican la entidad Usuario, solo agregan los campos que el listado
// administrativo necesita y que CU01 no expone (is_active, created_at).

import { RolUsuario } from '../shared/models/usuario.model';

export interface UsuarioAdmin {
  id: number;
  nombre: string;
  correo: string;
  rol: RolUsuario;
  is_active: boolean;
  created_at: string;
}

// CLIENTE se crea mediante CU02 (registro público), no desde CU05.
export type RolAsignableCU05 = Exclude<RolUsuario, 'CLIENTE'>;

export interface RolDisponible {
  valor: RolAsignableCU05;
  etiqueta: string;
}

export interface UsuarioCrearPayload {
  nombre: string;
  correo: string;
  password: string;
  rol: RolAsignableCU05;
}

export interface UsuarioActualizarPayload {
  nombre: string;
  correo: string;
}

export type CatalogStatusFilter = 'all' | 'active' | 'inactive';

export interface UsuariosListQuery {
  search?: string;
  rol?: RolUsuario;
  estado?: CatalogStatusFilter;
}
