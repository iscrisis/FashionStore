import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { AgregarDetallePayload, CrearReservaPayload, ReservaOut } from './crear-reserva.model';

/** Consume CU17 -- Crear reserva de prendas. Requiere un CLIENTE autenticado
 * (el interceptor HTTP ya adjunta el Bearer token, ver
 * core/interceptors/auth.interceptor.ts). */
@Injectable({ providedIn: 'root' })
export class CrearReservaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/reservas`;

  crear(payload: CrearReservaPayload): Observable<ReservaOut> {
    return this.http.post<ReservaOut>(this.baseUrl, payload);
  }

  /** Reservas PROPIAS en `sucursalId` a las que hoy se les podría agregar
   * una prenda más (estado_general PENDIENTE, ver GET /reservas/compatibles
   * en el backend) -- lista vacía si no hay ninguna. */
  listarCompatibles(sucursalId: number): Observable<ReservaOut[]> {
    return this.http.get<ReservaOut[]>(`${this.baseUrl}/compatibles`, {
      params: { sucursal_id: sucursalId },
    });
  }

  /** "Agregar a esta reserva": crea SOLO un ReservaDetalle sobre una
   * cabecera ya existente, nunca una reserva nueva (ver POST
   * /reservas/{id}/detalles en el backend). */
  agregarDetalle(reservaId: number, payload: AgregarDetallePayload): Observable<ReservaOut> {
    return this.http.post<ReservaOut>(`${this.baseUrl}/${reservaId}/detalles`, payload);
  }
}
