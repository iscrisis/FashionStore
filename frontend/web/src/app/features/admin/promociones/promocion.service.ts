import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { PromocionDetalle, PromocionListado, PromocionPayload } from './promocion.model';

/** Consume CU32 -- Gestionar promociones. Requiere un ADMINISTRADOR
 * autenticado (el interceptor HTTP ya adjunta el Bearer token). Sin DELETE:
 * "desactivar" es la única baja posible (ver backend, service.py -- no
 * existe ningún método que borre una promoción). */
@Injectable({ providedIn: 'root' })
export class PromocionService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/promociones`;

  list(): Observable<PromocionListado[]> {
    return this.http.get<PromocionListado[]>(this.baseUrl);
  }

  get(id: number): Observable<PromocionDetalle> {
    return this.http.get<PromocionDetalle>(`${this.baseUrl}/${id}`);
  }

  create(payload: PromocionPayload): Observable<PromocionDetalle> {
    return this.http.post<PromocionDetalle>(this.baseUrl, payload);
  }

  update(id: number, payload: PromocionPayload): Observable<PromocionDetalle> {
    return this.http.put<PromocionDetalle>(`${this.baseUrl}/${id}`, payload);
  }

  deactivate(id: number): Observable<PromocionDetalle> {
    return this.http.patch<PromocionDetalle>(`${this.baseUrl}/${id}/desactivar`, {});
  }
}
