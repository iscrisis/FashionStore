import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  CatalogoProductosQuery,
  CategoriaPublica,
  ColeccionPublica,
  ColorPublico,
  ProductoPublico,
  TallaPublica,
} from './catalogo.model';

/** Consume el catálogo público de CU11 -- sin token, apto para Invitado y Cliente. */
@Injectable({ providedIn: 'root' })
export class CatalogoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/catalogo`;

  listCategorias(): Observable<CategoriaPublica[]> {
    return this.http.get<CategoriaPublica[]>(`${this.baseUrl}/categorias`);
  }

  listColecciones(temporadaId?: number): Observable<ColeccionPublica[]> {
    let params = new HttpParams();
    if (temporadaId) {
      params = params.set('temporada_id', temporadaId);
    }
    return this.http.get<ColeccionPublica[]>(`${this.baseUrl}/colecciones`, { params });
  }

  listTallas(): Observable<TallaPublica[]> {
    return this.http.get<TallaPublica[]>(`${this.baseUrl}/tallas`);
  }

  listColores(): Observable<ColorPublico[]> {
    return this.http.get<ColorPublico[]>(`${this.baseUrl}/colores`);
  }

  listProductos(query?: CatalogoProductosQuery): Observable<ProductoPublico[]> {
    let params = new HttpParams();
    if (query?.search) {
      params = params.set('search', query.search);
    }
    if (query?.categoria_id) {
      params = params.set('categoria_id', query.categoria_id);
    }
    if (query?.coleccion_id) {
      params = params.set('coleccion_id', query.coleccion_id);
    }
    if (query?.talla_id) {
      params = params.set('talla_id', query.talla_id);
    }
    if (query?.color_id) {
      params = params.set('color_id', query.color_id);
    }
    return this.http.get<ProductoPublico[]>(`${this.baseUrl}/productos`, { params });
  }

  getProducto(id: number): Observable<ProductoPublico> {
    return this.http.get<ProductoPublico>(`${this.baseUrl}/productos/${id}`);
  }
}
