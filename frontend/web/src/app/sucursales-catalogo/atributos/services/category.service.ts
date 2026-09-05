import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { CatalogListQuery } from '../models/catalog-status-filter.model';
import { Category, CategoryPayload } from '../models/category.model';

@Injectable({ providedIn: 'root' })
export class CategoryService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/categories`;

  list(query?: CatalogListQuery): Observable<Category[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.status && query.status !== 'all') {
      params = params.set('status', query.status);
    }
    return this.http.get<Category[]>(this.baseUrl, { params });
  }

  get(id: number): Observable<Category> {
    return this.http.get<Category>(`${this.baseUrl}/${id}`);
  }

  create(payload: CategoryPayload): Observable<Category> {
    return this.http.post<Category>(this.baseUrl, payload);
  }

  update(id: number, payload: CategoryPayload): Observable<Category> {
    return this.http.put<Category>(`${this.baseUrl}/${id}`, payload);
  }

  setActive(id: number, isActive: boolean): Observable<Category> {
    return this.http.patch<Category>(`${this.baseUrl}/${id}/status`, { isActive });
  }
}
