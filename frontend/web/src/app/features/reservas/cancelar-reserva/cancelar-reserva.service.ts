import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ReservaDetalleOut } from '../crear-reserva/crear-reserva.model';

/** Consume CU19 -- Cancelar reserva. Requiere un CLIENTE autenticado (el
 * interceptor HTTP ya adjunta el Bearer token, ver
 * core/interceptors/auth.interceptor.ts). El backend resuelve el dueño de la
 * reserva SIEMPRE desde el token -- este servicio nunca envía cliente_id.
 *
 * Cancela un DETALLE (una prenda dentro de una reserva) sin afectar al
 * resto -- ver PATCH /reservas/detalles/{id}/cancelar en el backend
 * (CU19_CancelarReserva/router.py). Cancelar la reserva ENTERA existe en el
 * backend (PATCH /reservas/{id}/cancelar) pero no se expone todavía en esta
 * UI -- el mockup de CU19 solo pide cancelar por prenda. */
@Injectable({ providedIn: 'root' })
export class CancelarReservaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/reservas`;

  cancelarDetalle(detalleId: number): Observable<ReservaDetalleOut> {
    return this.http.patch<ReservaDetalleOut>(`${this.baseUrl}/detalles/${detalleId}/cancelar`, {});
  }
}
