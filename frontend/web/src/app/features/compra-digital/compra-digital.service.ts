import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ConfirmarCompraPayload, ResumenCompraOut, SucursalCompraOut, VentaOut } from './compra-digital.model';

/** Consume CU22 -- Realizar compra digital. Requiere un CLIENTE autenticado
 * (el interceptor HTTP ya adjunta el Bearer token). El backend obtiene los
 * items SIEMPRE del carrito propio del cliente autenticado (los que ya
 * quedaron `seleccionado` en CU21) -- este servicio nunca envía item_ids ni
 * cliente_id; tampoco envía precios ni el total, FastAPI los recalcula
 * siempre al confirmar. */
@Injectable({ providedIn: 'root' })
export class CompraDigitalService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/compra-digital`;

  obtenerResumen(): Observable<ResumenCompraOut> {
    return this.http.get<ResumenCompraOut>(`${this.baseUrl}/resumen`);
  }

  listarSucursales(ciudadId: number): Observable<SucursalCompraOut[]> {
    const params = new HttpParams().set('ciudad_id', ciudadId);
    return this.http.get<SucursalCompraOut[]>(`${this.baseUrl}/sucursales`, { params });
  }

  confirmar(payload: ConfirmarCompraPayload): Observable<VentaOut> {
    return this.http.post<VentaOut>(this.baseUrl, payload);
  }
}
