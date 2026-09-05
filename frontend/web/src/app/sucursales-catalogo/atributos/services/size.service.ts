import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { CatalogListQuery } from '../models/catalog-status-filter.model';
import { Size, SizePayload } from '../models/size.model';

@Injectable({ providedIn: 'root' })
export class SizeService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/tallas`;

  list(query?: CatalogListQuery): Observable<Size[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.estado && query.estado !== 'all') {
      params = params.set('estado', query.estado);
    }
    return this.http.get<Size[]>(this.baseUrl, { params });
  }

  create(payload: SizePayload): Observable<Size> {
    return this.http.post<Size>(this.baseUrl, payload);
  }

  update(id: number, payload: SizePayload): Observable<Size> {
    return this.http.put<Size>(`${this.baseUrl}/${id}`, payload);
  }

  setActive(id: number, isActive: boolean): Observable<Size> {
    return this.http.patch<Size>(`${this.baseUrl}/${id}/estado`, { is_active: isActive });
  }
}
