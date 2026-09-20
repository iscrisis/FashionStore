import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ReservaPanel } from '../../encargado/reservas/reservas.model';

/** Consume la integración mínima de CU20 con el rol Cajero -- requiere un
 * CAJERO autenticado (el interceptor HTTP ya adjunta el Bearer token, ver
 * core/interceptors/auth.interceptor.ts). El backend resuelve la sucursal
 * SIEMPRE desde el token -- este servicio nunca envía sucursal_id. Solo
 * consulta: no crea venta ni pago (CU24/CU25, fuera de alcance).
 *
 * Devuelve cabeceras AGRUPADAS (ReservaPanel, la misma forma que usa el
 * panel del Encargado) cuyo estado_general YA es LISTA_PARA_CAJA -- nunca
 * una reserva todavía EN_ATENCION, aunque alguna de sus prendas ya tenga
 * esa decisión tomada -- con `detalles` ya filtrado a solo las prendas que
 * sí van a caja (ver CU20_AtenderReservaPrendas/service.py:
 * listar_pendientes_cajero en el backend). */
@Injectable({ providedIn: 'root' })
export class ReservasPendientesService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/reservas`;

  listarPendientes(): Observable<ReservaPanel[]> {
    return this.http.get<ReservaPanel[]>(`${this.baseUrl}/cajero/pendientes`);
  }
}
