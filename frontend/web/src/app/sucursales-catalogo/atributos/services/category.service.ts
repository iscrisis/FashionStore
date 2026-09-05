import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { CatalogListQuery } from '../models/catalog-status-filter.model';
import { Category, CategoryPayload } from '../models/category.model';

@Injectable({ providedIn: 'root' })
export class CategoryService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/categorias`;

  list(query?: CatalogListQuery): Observable<Category[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.estado && query.estado !== 'all') {
      params = params.set('estado', query.estado);
    }
    return this.http.get<Category[]>(this.baseUrl, { params });
  }

  create(payload: CategoryPayload): Observable<Category> {
    return this.http.post<Category>(this.baseUrl, payload);
  }

  update(id: number, payload: CategoryPayload): Observable<Category> {
    return this.http.put<Category>(`${this.baseUrl}/${id}`, payload);
  }

  setActive(id: number, isActive: boolean): Observable<Category> {
    return this.http.patch<Category>(`${this.baseUrl}/${id}/estado`, { is_active: isActive });
  }

  setImagen(id: number, archivo: File): Observable<Category> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    return this.http.post<Category>(`${this.baseUrl}/${id}/imagen`, formData);
  }

  removeImagen(id: number): Observable<Category> {
    return this.http.delete<Category>(`${this.baseUrl}/${id}/imagen`);
  }
}
