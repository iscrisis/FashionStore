import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Temporada, TemporadaPayload, TemporadasListQuery } from './temporada-coleccion.model';

@Injectable({ providedIn: 'root' })
export class TemporadaAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/temporadas`;

  list(query?: TemporadasListQuery): Observable<Temporada[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.estado && query.estado !== 'all') {
      params = params.set('estado', query.estado);
    }
    return this.http.get<Temporada[]>(this.baseUrl, { params });
  }

  create(payload: TemporadaPayload): Observable<Temporada> {
    return this.http.post<Temporada>(this.baseUrl, payload);
  }

  update(id: number, payload: TemporadaPayload): Observable<Temporada> {
    return this.http.put<Temporada>(`${this.baseUrl}/${id}`, payload);
  }

  setActive(id: number, isActive: boolean): Observable<Temporada> {
    return this.http.patch<Temporada>(`${this.baseUrl}/${id}/estado`, { is_active: isActive });
  }
}
