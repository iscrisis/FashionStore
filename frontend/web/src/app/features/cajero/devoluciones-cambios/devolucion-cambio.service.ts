import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  CambioOut,
  DevolucionOut,
  RegistrarCambioPayload,
  RegistrarDevolucionPayload,
  VarianteCambioOut,
  VentaDevolucionOut,
} from './devolucion-cambio.model';

/** Consume CU26 (Registrar devolución o cambio). Requiere un CAJERO
 * autenticado (el interceptor HTTP ya adjunta el Bearer token). El backend
 * resuelve la sucursal y el cajero SIEMPRE desde el token -- este servicio
 * nunca envía sucursal_id ni cajero_id; tampoco precios ni montos de
 * reembolso, FastAPI los calcula/verifica siempre del lado del servidor. */
@Injectable({ providedIn: 'root' })
export class DevolucionCambioService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/devoluciones-cambios`;

  buscarVenta(codigoVenta: string): Observable<VentaDevolucionOut> {
    const params = new HttpParams().set('codigo_venta', codigoVenta);
    return this.http.get<VentaDevolucionOut>(`${this.baseUrl}/buscar`, { params });
  }

  opcionesCambio(ventaId: number, ventaDetalleId: number): Observable<VarianteCambioOut[]> {
    return this.http.get<VarianteCambioOut[]>(
      `${this.baseUrl}/${ventaId}/opciones-cambio/${ventaDetalleId}`,
    );
  }

  registrarDevolucion(payload: RegistrarDevolucionPayload): Observable<DevolucionOut> {
    return this.http.post<DevolucionOut>(`${this.baseUrl}/devolucion`, payload);
  }

  registrarCambio(payload: RegistrarCambioPayload): Observable<CambioOut> {
    return this.http.post<CambioOut>(`${this.baseUrl}/cambio`, payload);
  }
}
