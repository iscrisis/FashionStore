import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { FiltroHistorial, VentaHistorialOut } from './historial-compras.model';

/** Consume CU27 -- Consultar historial de compras. Requiere un CLIENTE o un
 * CAJERO autenticado (el interceptor HTTP ya adjunta el Bearer token). El
 * backend resuelve SIEMPRE del token de quién son las ventas -- este
 * servicio nunca envía cliente_id ni sucursal_id, solo los filtros
 * (fecha/código). Compartido entre features/cliente/historial-compras y
 * features/cajero/historial -- un único servicio, nunca duplicado. */
@Injectable({ providedIn: 'root' })
export class HistorialComprasService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/historial-compras`;

  private construirParams(filtro: FiltroHistorial): HttpParams {
    let params = new HttpParams();
    if (filtro.desde) {
      params = params.set('desde', filtro.desde);
    }
    if (filtro.hasta) {
      params = params.set('hasta', filtro.hasta);
    }
    if (filtro.codigo_venta) {
      params = params.set('codigo_venta', filtro.codigo_venta);
    }
    return params;
  }

  listarMias(filtro: FiltroHistorial): Observable<VentaHistorialOut[]> {
    return this.http.get<VentaHistorialOut[]>(`${this.baseUrl}/mias`, { params: this.construirParams(filtro) });
  }

  listarSucursal(filtro: FiltroHistorial): Observable<VentaHistorialOut[]> {
    return this.http.get<VentaHistorialOut[]>(`${this.baseUrl}/sucursal`, {
      params: this.construirParams(filtro),
    });
  }
}
