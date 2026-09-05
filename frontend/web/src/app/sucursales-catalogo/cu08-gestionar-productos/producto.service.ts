import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  Producto,
  ProductoPayload,
  ProductosListQuery,
  PropuestaProveedor,
} from './producto.model';

@Injectable({ providedIn: 'root' })
export class ProductoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/productos`;

  list(query?: ProductosListQuery): Observable<Producto[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.categoria_id) {
      params = params.set('categoria_id', query.categoria_id);
    }
    if (query?.temporada_id) {
      params = params.set('temporada_id', query.temporada_id);
    }
    if (query?.coleccion_id) {
      params = params.set('coleccion_id', query.coleccion_id);
    }
    if (query?.proveedor_id) {
      params = params.set('proveedor_id', query.proveedor_id);
    }
    if (query?.estado && query.estado !== 'all') {
      params = params.set('estado', query.estado);
    }
    return this.http.get<Producto[]>(this.baseUrl, { params });
  }

  create(payload: ProductoPayload): Observable<Producto> {
    return this.http.post<Producto>(this.baseUrl, payload);
  }

  update(id: number, payload: ProductoPayload): Observable<Producto> {
    return this.http.put<Producto>(`${this.baseUrl}/${id}`, payload);
  }

  setActive(id: number, isActive: boolean): Observable<Producto> {
    return this.http.patch<Producto>(`${this.baseUrl}/${id}/estado`, { is_active: isActive });
  }

  listPropuestas(proveedorId?: number): Observable<PropuestaProveedor[]> {
    let params = new HttpParams();
    if (proveedorId) {
      params = params.set('proveedor_id', proveedorId);
    }
    return this.http.get<PropuestaProveedor[]>(`${this.baseUrl}/propuestas`, { params });
  }

  setImagenPrincipal(id: number, archivo: File): Observable<Producto> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    return this.http.post<Producto>(`${this.baseUrl}/${id}/imagen-principal`, formData);
  }

  addImagen(id: number, archivo: File): Observable<Producto> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    return this.http.post<Producto>(`${this.baseUrl}/${id}/imagenes`, formData);
  }

  removeImagen(id: number, imagenId: number): Observable<Producto> {
    return this.http.delete<Producto>(`${this.baseUrl}/${id}/imagenes/${imagenId}`);
  }
}
