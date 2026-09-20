import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ActualizarSeleccionPayload, AgregarItemPayload, CarritoOut } from './carrito.model';

/** Consume CU21 -- Usar carrito de compras. Requiere un CLIENTE autenticado
 * (el interceptor HTTP ya adjunta el Bearer token, ver
 * core/interceptors/auth.interceptor.ts). El backend resuelve el dueño del
 * carrito SIEMPRE desde el token -- este servicio nunca envía cliente_id.
 * Cada mutación devuelve el carrito COMPLETO ya actualizado (nunca un item
 * aislado), mismo criterio que CU17/CU19/CU20 al devolver su cabecera. */
@Injectable({ providedIn: 'root' })
export class CarritoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/carrito`;

  consultar(): Observable<CarritoOut> {
    return this.http.get<CarritoOut>(this.baseUrl);
  }

  agregarItem(payload: AgregarItemPayload): Observable<CarritoOut> {
    return this.http.post<CarritoOut>(`${this.baseUrl}/items`, payload);
  }

  actualizarSeleccion(itemId: number, payload: ActualizarSeleccionPayload): Observable<CarritoOut> {
    return this.http.patch<CarritoOut>(`${this.baseUrl}/items/${itemId}`, payload);
  }

  eliminarItem(itemId: number): Observable<CarritoOut> {
    return this.http.delete<CarritoOut>(`${this.baseUrl}/items/${itemId}`);
  }
}
