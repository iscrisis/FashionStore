import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Coleccion, ColeccionPayload, ColeccionesListQuery } from './temporada-coleccion.model';

@Injectable({ providedIn: 'root' })
export class ColeccionAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/colecciones`;

  list(query?: ColeccionesListQuery): Observable<Coleccion[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.temporada_id) {
      params = params.set('temporada_id', query.temporada_id);
    }
    if (query?.estado && query.estado !== 'all') {
      params = params.set('estado', query.estado);
    }
    return this.http.get<Coleccion[]>(this.baseUrl, { params });
  }

  create(payload: ColeccionPayload): Observable<Coleccion> {
    return this.http.post<Coleccion>(this.baseUrl, payload);
  }

  update(id: number, payload: ColeccionPayload): Observable<Coleccion> {
    return this.http.put<Coleccion>(`${this.baseUrl}/${id}`, payload);
  }

  setActive(id: number, isActive: boolean): Observable<Coleccion> {
    return this.http.patch<Coleccion>(`${this.baseUrl}/${id}/estado`, { is_active: isActive });
  }
}
