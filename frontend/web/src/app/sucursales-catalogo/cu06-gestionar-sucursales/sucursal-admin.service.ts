import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  CatalogStatusFilter,
  Ciudad,
  CiudadCrearPayload,
  SucursalActualizarPayload,
  SucursalAdmin,
  SucursalCrearPayload,
  SucursalesListQuery,
} from './sucursal-admin.model';

@Injectable({ providedIn: 'root' })
export class SucursalAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/sucursales`;

  list(query?: SucursalesListQuery): Observable<SucursalAdmin[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.ciudad_id) {
      params = params.set('ciudad_id', query.ciudad_id);
    }
    if (query?.estado && query.estado !== 'all') {
      params = params.set('estado', query.estado);
    }
    return this.http.get<SucursalAdmin[]>(this.baseUrl, { params });
  }

  ciudades(estado?: CatalogStatusFilter): Observable<Ciudad[]> {
    let params = new HttpParams();
    if (estado && estado !== 'all') {
      params = params.set('estado', estado);
    }
    return this.http.get<Ciudad[]>(`${environment.apiUrl}/ciudades`, { params });
  }

  createCiudad(payload: CiudadCrearPayload): Observable<Ciudad> {
    return this.http.post<Ciudad>(`${environment.apiUrl}/ciudades`, payload);
  }

  setCiudadActive(id: number, isActive: boolean): Observable<Ciudad> {
    return this.http.patch<Ciudad>(`${environment.apiUrl}/ciudades/${id}/estado`, {
      is_active: isActive,
    });
  }

  create(payload: SucursalCrearPayload): Observable<SucursalAdmin> {
    return this.http.post<SucursalAdmin>(this.baseUrl, payload);
  }

  update(id: number, payload: SucursalActualizarPayload): Observable<SucursalAdmin> {
    return this.http.put<SucursalAdmin>(`${this.baseUrl}/${id}`, payload);
  }

  setActive(id: number, isActive: boolean): Observable<SucursalAdmin> {
    return this.http.patch<SucursalAdmin>(`${this.baseUrl}/${id}/estado`, {
      is_active: isActive,
    });
  }
}
