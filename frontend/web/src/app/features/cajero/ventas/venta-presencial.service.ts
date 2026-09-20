import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ConfirmarPagoPayload,
  CrearVentaDirectaPayload,
  PagoConfirmadoOut,
  ProductoBusquedaOut,
  VentaPresencialOut,
} from './venta-presencial.model';

/** Consume CU24 (Registrar venta presencial) y CU25 (Procesar pago
 * presencial) -- ambos sobre la MISMA Venta, un solo servicio (no
 * duplicado). Requiere un CAJERO autenticado (el interceptor HTTP ya
 * adjunta el Bearer token). El backend resuelve la sucursal y el cajero
 * SIEMPRE desde el token -- este servicio nunca envía sucursal_id ni
 * cajero_id; tampoco precios, total ni estado, FastAPI los calcula/verifica
 * siempre del lado del servidor. */
@Injectable({ providedIn: 'root' })
export class VentaPresencialService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/ventas-presenciales`;
  private readonly baseUrlPagos = `${environment.apiUrl}/pagos-presenciales`;

  buscarProductos(nombre: string): Observable<ProductoBusquedaOut[]> {
    const params = new HttpParams().set('nombre', nombre);
    return this.http.get<ProductoBusquedaOut[]>(`${this.baseUrl}/productos`, { params });
  }

  crearVentaDirecta(payload: CrearVentaDirectaPayload): Observable<VentaPresencialOut> {
    return this.http.post<VentaPresencialOut>(`${this.baseUrl}/directa`, payload);
  }

  crearVentaDesdeReserva(reservaId: number): Observable<VentaPresencialOut> {
    return this.http.post<VentaPresencialOut>(`${this.baseUrl}/desde-reserva/${reservaId}`, {});
  }

  confirmarPago(ventaId: number, payload: ConfirmarPagoPayload): Observable<PagoConfirmadoOut> {
    return this.http.post<PagoConfirmadoOut>(`${this.baseUrlPagos}/${ventaId}/confirmar`, payload);
  }
}
