import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ConsultaInteligenteRequest,
  ConsultaInteligenteResponse,
  InventarioReporte,
  ProductosMasVendidosReporte,
  ReportesFiltro,
  ReservasReporte,
  ResumenReporte,
  VentasReporte,
} from './reportes.model';

/** Consume CU30 -- SOLO ADMINISTRADOR (el backend valida el rol vía JWT,
 * nunca confía en Angular). El filtrado (fechas/sucursal) se resuelve
 * SIEMPRE en FastAPI -- este servicio nunca descarga datos crudos para
 * filtrarlos acá. */
@Injectable({ providedIn: 'root' })
export class ReportesService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/reportes`;

  private params(filtro: ReportesFiltro, incluirFechas: boolean): HttpParams {
    let params = new HttpParams();
    if (incluirFechas && filtro.fecha_desde) {
      params = params.set('fecha_desde', filtro.fecha_desde);
    }
    if (incluirFechas && filtro.fecha_hasta) {
      params = params.set('fecha_hasta', filtro.fecha_hasta);
    }
    if (filtro.sucursal_id) {
      params = params.set('sucursal_id', filtro.sucursal_id);
    }
    return params;
  }

  resumen(filtro: ReportesFiltro): Observable<ResumenReporte> {
    return this.http.get<ResumenReporte>(`${this.baseUrl}/resumen`, { params: this.params(filtro, true) });
  }

  ventas(filtro: ReportesFiltro): Observable<VentasReporte> {
    return this.http.get<VentasReporte>(`${this.baseUrl}/ventas`, { params: this.params(filtro, true) });
  }

  // /inventario ignora fecha_desde/fecha_hasta por diseño -- es una foto del
  // stock ACTUAL, sin dimensión temporal en el modelo (ver backend/service.py).
  inventario(filtro: ReportesFiltro): Observable<InventarioReporte> {
    return this.http.get<InventarioReporte>(`${this.baseUrl}/inventario`, { params: this.params(filtro, false) });
  }

  reservas(filtro: ReportesFiltro): Observable<ReservasReporte> {
    return this.http.get<ReservasReporte>(`${this.baseUrl}/reservas`, { params: this.params(filtro, true) });
  }

  productosMasVendidos(filtro: ReportesFiltro): Observable<ProductosMasVendidosReporte> {
    return this.http.get<ProductosMasVendidosReporte>(`${this.baseUrl}/productos-mas-vendidos`, {
      params: this.params(filtro, true),
    });
  }

  // CU30 -- segunda parte: consulta inteligente (texto/voz + Gemini). Único
  // punto por el que Angular pide la interpretación -- nunca llama a
  // Gemini directamente (ver backend/gemini_client.py).
  consultaInteligente(payload: ConsultaInteligenteRequest): Observable<ConsultaInteligenteResponse> {
    return this.http.post<ConsultaInteligenteResponse>(`${this.baseUrl}/consulta-inteligente`, payload);
  }
}
