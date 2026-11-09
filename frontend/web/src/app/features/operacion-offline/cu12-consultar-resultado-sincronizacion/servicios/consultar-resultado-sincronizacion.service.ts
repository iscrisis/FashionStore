import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { environment } from '../../../../../environments/environment';
import {
  ResultadoSincronizacion,
  ResumenResultados,
} from '../modelos/resultado-sincronizacion.model';

/**
 * CU12 — Consultar resultado de sincronización.
 *
 * Consulta qué pasó con una operación enviada por CU11.
 * Recupera información persistida en PostgreSQL sin ejecutar nuevas sincronizaciones.
 */
@Injectable({ providedIn: 'root' })
export class ConsultarResultadoSincronizacionService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/resultados-sincronizacion`;

  /**
   * Consultar resultado de una venta offline.
   */
  consultarResultadoVenta(uuidLocal: string) {
    return this.http.get<ResultadoSincronizacion>(
      `${this.baseUrl}/venta/${uuidLocal}`
    );
  }

  /**
   * Consultar resultado de una reserva offline.
   */
  consultarResultadoReserva(uuidLocal: string) {
    return this.http.get<ResultadoSincronizacion>(
      `${this.baseUrl}/reserva/${uuidLocal}`
    );
  }

  /**
   * Listar todas las ventas sincronizadas.
   */
  listarResultadosVentas() {
    return this.http.get<ResultadoSincronizacion[]>(
      `${this.baseUrl}/ventas`
    );
  }

  /**
   * Listar todas las reservas sincronizadas.
   */
  listarResultadosReservas() {
    return this.http.get<ResultadoSincronizacion[]>(
      `${this.baseUrl}/reservas`
    );
  }

  /**
   * Obtener resumen de conteos de resultados.
   */
  obtenerResumen() {
    return this.http.get<ResumenResultados>(
      `${this.baseUrl}/resumen`
    );
  }
}
