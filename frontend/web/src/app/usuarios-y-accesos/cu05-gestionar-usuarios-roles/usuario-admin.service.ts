import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  CiudadOpcion,
  ProveedorOpcion,
  RolDisponible,
  SucursalOpcion,
  UsuarioActualizarPayload,
  UsuarioAdmin,
  UsuarioCrearPayload,
  UsuariosListQuery,
} from './usuario-admin.model';

@Injectable({ providedIn: 'root' })
export class UsuarioAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/usuarios`;

  // Ciudad → Sucursal provienen de CU06 (P1_SucursalesYCatalogos): CU05 solo
  // las consulta para el selector de "Nuevo/Editar usuario", no las administra.
  ciudades(): Observable<CiudadOpcion[]> {
    const params = new HttpParams().set('estado', 'active');
    return this.http.get<CiudadOpcion[]>(`${environment.apiUrl}/ciudades`, { params });
  }

  sucursalesPorCiudad(ciudadId: number): Observable<SucursalOpcion[]> {
    const params = new HttpParams().set('ciudad_id', ciudadId).set('estado', 'active');
    return this.http.get<SucursalOpcion[]>(`${environment.apiUrl}/sucursales`, { params });
  }

  // Proveedor viene de Gestión de Proveedores (P1_SucursalesYCatalogos): CU05
  // solo lo consulta para vincular una cuenta PROVEEDOR, no lo administra.
  proveedores(): Observable<ProveedorOpcion[]> {
    const params = new HttpParams().set('estado', 'active');
    return this.http.get<ProveedorOpcion[]>(`${environment.apiUrl}/proveedores`, { params });
  }

  list(query?: UsuariosListQuery): Observable<UsuarioAdmin[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.rol) {
      params = params.set('rol', query.rol);
    }
    if (query?.estado && query.estado !== 'all') {
      params = params.set('estado', query.estado);
    }
    return this.http.get<UsuarioAdmin[]>(this.baseUrl, { params });
  }

  roles(): Observable<RolDisponible[]> {
    return this.http.get<RolDisponible[]>(`${this.baseUrl}/roles`);
  }

  create(payload: UsuarioCrearPayload): Observable<UsuarioAdmin> {
    return this.http.post<UsuarioAdmin>(this.baseUrl, payload);
  }

  update(id: number, payload: UsuarioActualizarPayload): Observable<UsuarioAdmin> {
    return this.http.put<UsuarioAdmin>(`${this.baseUrl}/${id}`, payload);
  }

  changeRole(id: number, rol: string): Observable<UsuarioAdmin> {
    return this.http.patch<UsuarioAdmin>(`${this.baseUrl}/${id}/rol`, { rol });
  }

  setActive(id: number, isActive: boolean): Observable<UsuarioAdmin> {
    return this.http.patch<UsuarioAdmin>(`${this.baseUrl}/${id}/estado`, {
      is_active: isActive,
    });
  }
}
