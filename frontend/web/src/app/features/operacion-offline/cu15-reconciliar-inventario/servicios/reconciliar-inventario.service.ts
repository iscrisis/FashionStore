import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { environment } from '../../../../../environments/environment';

interface ResultadoReconciliacion {
  uuid_operacion_offline: string;
  tipo_operacion: 'VENTA_OFFLINE' | 'RESERVA_OFFLINE';
  estado_general: 'CONSISTENTE' | 'DIVERGENCIA_DETECTADA' | 'PENDIENTE_REVISION';
  detalles: Array<{
    producto_variante_id: number;
    cantidad_operacion: number;
    stock_actual: number;
    stock_esperado: number;
    diferencia: number;
    estado: string;
  }>;
  motivo_inconsistencia?: string;
  fecha_reconciliacion: string;
}

/**
 * CU15 — Reconciliar inventario.
 *
 * Verifica consistencia de inventario después de operaciones offline sincronizadas.
 * Ejecuta automáticamente sin intervención del usuario.
 *
 * NO modifica stock (solo verifica).
 * NO requiere confirmación del usuario.
 */
@Injectable({ providedIn: 'root' })
export class ReconciliarInventarioService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}`;

  /**
   * Reconciliar una venta confirmada (automático, sin interfaz).
   *
   * Verifica que el stock se descontó correctamente después de CU11.
   */
  async reconciliarVentaAuto(
    uuidOperacion: string,
    empresaId: number,
  ): Promise<ResultadoReconciliacion | null> {
    try {
      // Reconciliación automática: sin interferir si falla
      const resultado = (await this.http
        .post<ResultadoReconciliacion>(
          `${this.baseUrl}/reconciliar/ventas/${uuidOperacion}?empresa_id=${empresaId}`,
          {},
        )
        .toPromise()) as ResultadoReconciliacion;

      if (resultado?.estado_general === 'CONSISTENTE') {
        console.log(
          `[CU15] Venta reconciliada: ${uuidOperacion} -> CONSISTENTE`,
        );
      } else if (resultado?.estado_general === 'DIVERGENCIA_DETECTADA') {
        console.warn(
          `[CU15] Divergencia detectada: ${uuidOperacion} -> ${resultado.motivo_inconsistencia}`,
        );
      } else {
        console.info(
          `[CU15] Revisión manual requerida: ${uuidOperacion}`,
        );
      }

      return resultado;
    } catch (error) {
      // No lanzar error: CU15 es verificación, no crítica
      console.debug(`[CU15] Error reconciliando venta (no crítico): ${String(error)}`);
      return null;
    }
  }

  /**
   * Reconciliar una reserva confirmada (automático, sin interfaz).
   */
  async reconciliarReservaAuto(
    uuidOperacion: string,
    empresaId: number,
  ): Promise<ResultadoReconciliacion | null> {
    try {
      const resultado = (await this.http
        .post<ResultadoReconciliacion>(
          `${this.baseUrl}/reconciliar/reservas/${uuidOperacion}?empresa_id=${empresaId}`,
          {},
        )
        .toPromise()) as ResultadoReconciliacion;

      if (resultado?.estado_general === 'CONSISTENTE') {
        console.log(
          `[CU15] Reserva reconciliada: ${uuidOperacion} -> CONSISTENTE`,
        );
      } else if (resultado?.estado_general === 'DIVERGENCIA_DETECTADA') {
        console.warn(
          `[CU15] Divergencia en reserva: ${uuidOperacion} -> ${resultado.motivo_inconsistencia}`,
        );
      } else {
        console.info(
          `[CU15] Revisión manual requerida: ${uuidOperacion}`,
        );
      }

      return resultado;
    } catch (error) {
      console.debug(`[CU15] Error reconciliando reserva (no crítico): ${String(error)}`);
      return null;
    }
  }
}
