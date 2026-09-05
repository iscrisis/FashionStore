import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { CatalogListQuery } from '../models/catalog-status-filter.model';
import { ColorItem, ColorPayload } from '../models/color.model';

@Injectable({ providedIn: 'root' })
export class ColorService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/colors`;

  list(query?: CatalogListQuery): Observable<ColorItem[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.status && query.status !== 'all') {
      params = params.set('status', query.status);
    }
    return this.http.get<ColorItem[]>(this.baseUrl, { params });
  }

  get(id: number): Observable<ColorItem> {
    return this.http.get<ColorItem>(`${this.baseUrl}/${id}`);
  }

  create(payload: ColorPayload): Observable<ColorItem> {
    return this.http.post<ColorItem>(this.baseUrl, payload);
  }

  update(id: number, payload: ColorPayload): Observable<ColorItem> {
    return this.http.put<ColorItem>(`${this.baseUrl}/${id}`, payload);
  }

  setActive(id: number, isActive: boolean): Observable<ColorItem> {
    return this.http.patch<ColorItem>(`${this.baseUrl}/${id}/status`, { isActive });
  }
}
