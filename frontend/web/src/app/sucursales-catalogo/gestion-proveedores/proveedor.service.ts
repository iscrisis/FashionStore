import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Proveedor, ProveedorPayload, ProveedoresListQuery } from './proveedor.model';

@Injectable({ providedIn: 'root' })
export class ProveedorService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/proveedores`;

  list(query?: ProveedoresListQuery): Observable<Proveedor[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.estado && query.estado !== 'all') {
      params = params.set('estado', query.estado);
    }
    return this.http.get<Proveedor[]>(this.baseUrl, { params });
  }

  create(payload: ProveedorPayload): Observable<Proveedor> {
    return this.http.post<Proveedor>(this.baseUrl, payload);
  }

  update(id: number, payload: ProveedorPayload): Observable<Proveedor> {
    return this.http.put<Proveedor>(`${this.baseUrl}/${id}`, payload);
  }

  setActive(id: number, isActive: boolean): Observable<Proveedor> {
    return this.http.patch<Proveedor>(`${this.baseUrl}/${id}/estado`, { is_active: isActive });
  }
}
