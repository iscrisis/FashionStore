import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../../environments/environment';
import { AuthService } from '../../../../core/services/auth.service';
import { OfflineStorageService } from '../../../../core/services/offline-storage.service';

/**
 * CU13 — Reintentar sincronización fallida.
 *
 * Permite reintentar operaciones (ventas/reservas) que fallaron en sincronización anterior.
 * Respeta:
 * - Límite máximo de reintentos (5)
 * - Backoff exponencial entre intentos
 * - Idempotencia (UUID nunca cambia)
 * - Multitenant (empresa_id validado)
 */
@Injectable({ providedIn: 'root' })
export class ReintentoOperacionesService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly offlineStorage = inject(OfflineStorageService);
  private readonly baseUrl = `${environment.apiUrl}`;

  /**
   * Reintentar sincronización de una venta fallida.
   *
   * Llama POST /reintentar/ventas/{uuid}
   * Retorna resultado de reintento (puede ser CONFIRMADA, RECHAZADA o CONFLICTO)
   */
  async reintentoVenta(ventaUuid: string, empresaId: number): Promise<any> {
    const usuario = this.auth.usuario();
    if (!usuario) {
      throw new Error('Usuario no autenticado');
    }

    try {
      console.log(`[CU13] Reintentando venta: ${ventaUuid}`);

      const payload = {
        empresa_id: empresaId,
        motivo_manual: 'Reintento manual del usuario',
      };

      const resultado = (await this.http
        .post(`${this.baseUrl}/reintentar/ventas/${ventaUuid}`, payload)
        .toPromise()) as any;

      console.log(`[CU13] Venta reintentada: ${ventaUuid} -> estado=${resultado.estado}`);

      // Actualizar IndexedDB con resultado
      if (resultado) {
        try {
          const estadoLocal =
            resultado.estado === 'CONFIRMADA' ? 'SINCRONIZADA' : resultado.estado;
          await this.offlineStorage.actualizarEstadoVentaOffline(
            ventaUuid,
            estadoLocal as 'SINCRONIZADA' | 'RECHAZADA' | 'CONFLICTO',
            resultado.motivo,
            {
              venta_id: resultado.venta_id,
              codigo_venta: resultado.codigo_venta,
            }
          );
        } catch (storageError) {
          console.error('[CU13] Error actualizando IndexedDB:', storageError);
        }
      }

      return resultado;
    } catch (error: any) {
      console.error(`[CU13] Error reintentando venta ${ventaUuid}:`, error);
      throw error;
    }
  }

  /**
   * Reintentar sincronización de una reserva fallida.
   */
  async reintentoReserva(reservaUuid: string, empresaId: number): Promise<any> {
    const usuario = this.auth.usuario();
    if (!usuario) {
      throw new Error('Usuario no autenticado');
    }

    try {
      console.log(`[CU13] Reintentando reserva: ${reservaUuid}`);

      const payload = {
        empresa_id: empresaId,
      };

      const resultado = (await this.http
        .post(`${this.baseUrl}/reintentar/reservas/${reservaUuid}`, payload)
        .toPromise()) as any;

      console.log(`[CU13] Reserva reintentada: ${reservaUuid} -> estado=${resultado.estado}`);

      // Actualizar IndexedDB
      if (resultado) {
        try {
          const estadoLocal =
            resultado.estado === 'CONFIRMADA' ? 'SINCRONIZADA' : resultado.estado;
          await this.offlineStorage.actualizarEstadoReservaOffline(
            reservaUuid,
            estadoLocal as 'SINCRONIZADA' | 'RECHAZADA' | 'CONFLICTO',
            resultado.motivo,
            {
              reserva_id: (resultado as any).reserva_id,
              codigo_reserva: (resultado as any).codigo_reserva,
            }
          );
        } catch (storageError) {
          console.error('[CU13] Error actualizando IndexedDB:', storageError);
        }
      }

      return resultado;
    } catch (error: any) {
      console.error(`[CU13] Error reintentando reserva ${reservaUuid}:`, error);
      throw error;
    }
  }

  /**
   * Calcular si una operación es elegible para reintentar (en base a backoff local).
   */
  esElegibleParaReintento(operacion: any): boolean {
    const now = Date.now();
    const proximoReintento = operacion.proximo_reintento_disponible_en_ms || 0;

    return proximoReintento <= now;
  }

  /**
   * Formato amigable del tiempo faltante para reintento.
   */
  formatearTiempoEspera(ms: number): string {
    if (ms <= 0) return 'Disponible ahora';

    const segundos = Math.ceil(ms / 1000);
    if (segundos < 60) return `${segundos}s`;

    const minutos = Math.ceil(segundos / 60);
    return `${minutos}m`;
  }
}
