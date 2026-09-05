import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { CiudadPublica, SucursalPublica } from './sucursal.model';

/** Consume la consulta pública de sucursales de CU07 -- sin token, apto para Invitado y Cliente. */
@Injectable({ providedIn: 'root' })
export class SucursalPublicaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/sucursales-publicas`;

  listCiudades(): Observable<CiudadPublica[]> {
    return this.http.get<CiudadPublica[]>(`${this.baseUrl}/ciudades`);
  }

  listSucursales(ciudadId?: number): Observable<SucursalPublica[]> {
    let params = new HttpParams();
    if (ciudadId) {
      params = params.set('ciudad_id', ciudadId);
    }
    return this.http.get<SucursalPublica[]>(`${this.baseUrl}/sucursales`, { params });
  }

  getSucursal(id: number): Observable<SucursalPublica> {
    return this.http.get<SucursalPublica>(`${this.baseUrl}/sucursales/${id}`);
  }
}
