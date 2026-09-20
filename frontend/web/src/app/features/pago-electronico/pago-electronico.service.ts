import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  CheckoutSessionOut,
  CrearCheckoutPayload,
  VentaPagadaOut,
  VerificarPagoPayload,
} from './pago-electronico.model';

/** Consume CU23 -- Procesar pago electrónico. Requiere un CLIENTE
 * autenticado (el interceptor HTTP ya adjunta el Bearer token). El backend
 * obtiene la Venta y su total SIEMPRE desde su propio id/registro -- este
 * servicio nunca envía monto, precio ni estado; con Stripe Checkout Hosted
 * tampoco maneja número de tarjeta, CVC ni fecha de vencimiento. */
@Injectable({ providedIn: 'root' })
export class PagoElectronicoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/pagos`;

  crearCheckout(payload: CrearCheckoutPayload): Observable<CheckoutSessionOut> {
    return this.http.post<CheckoutSessionOut>(`${this.baseUrl}/checkout`, payload);
  }

  verificarPago(payload: VerificarPagoPayload): Observable<VentaPagadaOut> {
    return this.http.post<VentaPagadaOut>(`${this.baseUrl}/verificar`, payload);
  }
}
