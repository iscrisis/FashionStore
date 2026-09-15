import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  MovimientoOut,
  ProductoConVariantes,
  RegistrarMovimientoPayload,
} from './movimientos-inventario.model';

@Injectable({ providedIn: 'root' })
export class MovimientosInventarioService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/movimientos-inventario/panel`;

  buscarProductos(search?: string): Observable<ProductoConVariantes[]> {
    let params = new HttpParams();
    if (search) {
      params = params.set('search', search);
    }
    return this.http.get<ProductoConVariantes[]>(`${this.baseUrl}/productos`, { params });
  }

  registrar(payload: RegistrarMovimientoPayload): Observable<MovimientoOut> {
    return this.http.post<MovimientoOut>(this.baseUrl, payload);
  }

  historial(limit = 50): Observable<MovimientoOut[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<MovimientoOut[]>(`${this.baseUrl}/historial`, { params });
  }
}
