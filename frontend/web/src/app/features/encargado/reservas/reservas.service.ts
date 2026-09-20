import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ReservaDetallePanel, ReservaPanel } from './reservas.model';

/** Consume CU20 -- Atender reserva de prendas. Requiere un
 * ENCARGADO_SUCURSAL autenticado (el interceptor HTTP ya adjunta el Bearer
 * token, ver core/interceptors/auth.interceptor.ts). El backend resuelve la
 * sucursal SIEMPRE desde el token -- este servicio nunca envía sucursal_id.
 *
 * Dos niveles, nunca mezclados (ver backend router.py):
 *   - `confirmarLlegada`/`finalizarAtencion`: UN botón por RESERVA
 *     (`/reservas/{id}/...`), devuelven la cabecera completa actualizada.
 *   - `preparar`/`noLaCompra`/`enviarACaja`: por PRENDA
 *     (`/reservas/detalles/{id}/...`), devuelven solo ese detalle. */
@Injectable({ providedIn: 'root' })
export class PanelReservasService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/reservas`;

  listarPanel(): Observable<ReservaPanel[]> {
    return this.http.get<ReservaPanel[]>(`${this.baseUrl}/panel`);
  }

  /** Integración mínima con el rol Cajero -- solo cabeceras cuyo
   * estado_general YA es LISTA_PARA_CAJA (ver reservas-pendientes en
   * features/cajero), con `detalles` ya filtrado a las prendas que sí van
   * a caja. */
  listarPendientesCajero(): Observable<ReservaPanel[]> {
    return this.http.get<ReservaPanel[]>(`${this.baseUrl}/cajero/pendientes`);
  }

  confirmarLlegada(reservaId: number): Observable<ReservaPanel> {
    return this.http.patch<ReservaPanel>(`${this.baseUrl}/${reservaId}/confirmar-llegada`, {});
  }

  finalizarAtencion(reservaId: number): Observable<ReservaPanel> {
    return this.http.patch<ReservaPanel>(`${this.baseUrl}/${reservaId}/finalizar-atencion`, {});
  }

  preparar(detalleId: number): Observable<ReservaDetallePanel> {
    return this.http.patch<ReservaDetallePanel>(`${this.baseUrl}/detalles/${detalleId}/preparar`, {});
  }

  noLaCompra(detalleId: number): Observable<ReservaDetallePanel> {
    return this.http.patch<ReservaDetallePanel>(`${this.baseUrl}/detalles/${detalleId}/no-la-compra`, {});
  }

  enviarACaja(detalleId: number): Observable<ReservaDetallePanel> {
    return this.http.patch<ReservaDetallePanel>(`${this.baseUrl}/detalles/${detalleId}/enviar-a-caja`, {});
  }
}
