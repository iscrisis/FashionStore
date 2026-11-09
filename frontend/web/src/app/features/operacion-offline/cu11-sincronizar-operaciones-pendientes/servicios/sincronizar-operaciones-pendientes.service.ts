import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, from } from 'rxjs';
import { environment } from '../../../../../environments/environment';
import { ConnectivityService } from '../../../../core/services/connectivity.service';
import { OfflineStorageService } from '../../../../core/services/offline-storage.service';
import { AuthService } from '../../../../core/services/auth.service';
import { ReconciliarInventarioService } from '../../cu15-reconciliar-inventario/servicios/reconciliar-inventario.service';

interface ResultadoSincronizacion {
  uuid_local: string;
  venta_id?: number | null;
  codigo_venta?: string | null;
  estado: 'CONFIRMADA' | 'RECHAZADA' | 'CONFLICTO';
  motivo?: string | null;
  total?: number | null;
  error?: string;
}

/**
 * CU11 — Sincronizar operaciones pendientes.
 *
 * Sincroniza ventas y reservas offline desde IndexedDB a FastAPI.
 * Garantías: idempotencia, atomicidad, aislamiento multitenant.
 */
@Injectable({ providedIn: 'root' })
export class SincronizarOperacionesPendientesService {
  private readonly http = inject(HttpClient);
  private readonly connectivity = inject(ConnectivityService);
  private readonly offlineStorage = inject(OfflineStorageService);
  private readonly auth = inject(AuthService);
  private readonly reconciliarInventario = inject(ReconciliarInventarioService);
  private readonly baseUrl = `${environment.apiUrl}`;

  /**
   * Sincronizar una venta presencial offline.
   *
   * Recupera venta + detalles + pago desde IndexedDB,
   * valida contexto, envía a FastAPI y actualiza estado.
   */
  async sincronizarVentaOffline(
    ventaUuid: string,
    empresaId: number,
  ): Promise<ResultadoSincronizacion> {
    try {
      // 1. Obtener venta desde IndexedDB por UUID
      const venta = await this.obtenerVentaPorUuid(ventaUuid, empresaId);
      if (!venta) {
        console.error(`[CU11] Venta no encontrada: ${ventaUuid}`);
        return { uuid_local: ventaUuid, estado: 'RECHAZADA', motivo: 'Venta no encontrada' };
      }

      // 2. Validar aislamiento (venta pertenece a empresa correcta)
      if (venta.empresa_id !== empresaId) {
        throw new Error('Empresa no autorizada');
      }

      // 3. Obtener detalles (están en ObjectStore separado, indexados por venta_uuid)
      const detalles = await this.offlineStorage.obtenerDetallesVenta(ventaUuid);
      if (!detalles || detalles.length === 0) {
        throw new Error('Venta sin detalles');
      }

      // 4. Obtener pago en efectivo (indexado por venta_uuid)
      const pago = await this.obtenerPagoVenta(ventaUuid);

      // 5. Construir payload para FastAPI
      const payload = {
        uuid: ventaUuid,
        tipo_operacion: 'VENTA_OFFLINE',
        empresa_id: venta.empresa_id,
        sucursal_id: venta.sucursal_id,
        fecha_operacion_local: venta.fecha_creacion,
        detalles: detalles.map((d: any) => ({
          producto_variante_id: d.producto_variante_id,
          cantidad: d.cantidad,
          precio_unitario: d.precio_unitario,
          subtotal: d.subtotal,
        })),
        metodo_pago: 'EFECTIVO',
        monto_recibido: pago?.monto_recibido,
        total: venta.total,
      };

      // 6. Enviar a FastAPI
      console.log(`[CU11] Sincronizando venta offline: ${ventaUuid}`);
      const resultado = (await this.http
        .post(`${this.baseUrl}/sincronizar/ventas`, payload)
        .toPromise()) as ResultadoSincronizacion;

      // 7. Procesar resultado y persistir en IndexedDB
      if (resultado) {
        try {
          const estadoLocal = resultado.estado === 'CONFIRMADA' ? 'SINCRONIZADA' : resultado.estado;
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
          console.error('[CU11] Error guardando resultado en IndexedDB:', storageError);
        }

        if (resultado.estado === 'CONFIRMADA') {
          console.log(
            `[CU11] Venta sincronizada: ${ventaUuid} -> venta_id=${resultado.venta_id}`,
          );
          // CU15: Reconciliar inventario automáticamente (no bloqueante)
          this.reconciliarInventario
            .reconciliarVentaAuto(ventaUuid, venta.empresa_id)
            .catch(() => {
              // Silenciar errores: CU15 es verificación, no crítica
            });
        } else if (resultado.estado === 'CONFLICTO') {
          console.warn(`[CU11] Conflicto: ${resultado.motivo}`);
        } else {
          console.error(`[CU11] Rechazada: ${resultado.motivo}`);
        }
      }

      return resultado;
    } catch (error) {
      console.error(`[CU11] Error sincronizando venta ${ventaUuid}:`, error);
      return { uuid_local: ventaUuid, estado: 'RECHAZADA', motivo: String(error) };
    }
  }

  /**
   * Obtener lista de todas las ventas pendientes de sincronización.
   */
  async obtenerVentasPendientes(empresaId: number): Promise<any[]> {
    try {
      const ventas = await this.offlineStorage.obtenerVentasOfflinePendientes(
        empresaId,
      );
      console.log(`[CU11] Ventas pendientes encontradas: ${ventas.length}`);
      return ventas || [];
    } catch (error) {
      console.error('[CU11] Error obteniendo ventas pendientes:', error);
      return [];
    }
  }

  /**
   * Obtener reservas pendientes de sincronización.
   */
  async obtenerReservasPendientes(
    empresaId: number,
  ): Promise<any[]> {
    try {
      const reservas =
        await this.offlineStorage.getReservasOfflinePendientes(empresaId);
      console.log(
        `[CU11] Reservas pendientes encontradas: ${reservas.length}`,
      );
      return reservas || [];
    } catch (error) {
      console.error('[CU11] Error obteniendo reservas pendientes:', error);
      return [];
    }
  }

  /**
   * Sincronizar una reserva presencial offline.
   *
   * Recupera reserva + detalles desde IndexedDB, valida contexto,
   * envía a FastAPI y actualiza estado.
   */
  async sincronizarReservaOffline(
    reservaUuid: string,
    empresaId: number,
  ): Promise<ResultadoSincronizacion> {
    try {
      // 1. Obtener reserva desde IndexedDB por UUID
      const reserva = await this.obtenerReservaPorUuid(reservaUuid, empresaId);
      if (!reserva) {
        console.error(`[CU11] Reserva no encontrada: ${reservaUuid}`);
        return { uuid_local: reservaUuid, estado: 'RECHAZADA', motivo: 'Reserva no encontrada' };
      }

      // 2. Validar aislamiento (reserva pertenece a empresa correcta)
      if (reserva.empresa_id !== empresaId) {
        throw new Error('Empresa no autorizada');
      }

      // 3. Obtener detalles (están en ObjectStore separado, indexados por reserva_uuid)
      const detalles = await this.offlineStorage.getDetallesReserva(reservaUuid);
      if (!detalles || detalles.length === 0) {
        throw new Error('Reserva sin detalles');
      }

      // 4. Construir payload para FastAPI
      const payload = {
        uuid: reservaUuid,
        tipo_operacion: 'RESERVA_OFFLINE',
        empresa_id: reserva.empresa_id,
        sucursal_id: reserva.sucursal_id,
        cliente_id: reserva.cliente_id,
        fecha_reserva: reserva.fecha_reserva,
        hora_inicio: reserva.hora_inicio,
        detalles: detalles.map((d: any) => ({
          producto_variante_id: d.producto_variante_id,
          cantidad: d.cantidad,
        })),
      };

      // 5. Enviar a FastAPI
      console.log(`[CU11] Sincronizando reserva offline: ${reservaUuid}`);
      const resultado = (await this.http
        .post(`${this.baseUrl}/sincronizar/reservas`, payload)
        .toPromise()) as ResultadoSincronizacion;

      // 6. Procesar resultado y persistir en IndexedDB
      if (resultado) {
        try {
          const estadoLocal = resultado.estado === 'CONFIRMADA' ? 'SINCRONIZADA' : resultado.estado;
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
          console.error('[CU11] Error guardando resultado en IndexedDB:', storageError);
        }

        if (resultado.estado === 'CONFIRMADA') {
          console.log(
            `[CU11] Reserva sincronizada: ${reservaUuid} -> reserva_id=${ (resultado as any).reserva_id}`,
          );
          // CU15: Reconciliar inventario automáticamente (no bloqueante)
          this.reconciliarInventario
            .reconciliarReservaAuto(reservaUuid, reserva.empresa_id)
            .catch(() => {
              // Silenciar errores: CU15 es verificación, no crítica
            });
        } else if (resultado.estado === 'CONFLICTO') {
          console.warn(`[CU11] Conflicto: ${resultado.motivo}`);
        } else {
          console.error(`[CU11] Rechazada: ${resultado.motivo}`);
        }
      }

      return resultado;
    } catch (error) {
      console.error(`[CU11] Error sincronizando reserva ${reservaUuid}:`, error);
      return { uuid_local: reservaUuid, estado: 'RECHAZADA', motivo: String(error) };
    }
  }

  /**
   * Obtener una reserva específica por UUID desde IndexedDB.
   */
  private async obtenerReservaPorUuid(
    reservaUuid: string,
    empresaId: number,
  ): Promise<any | null> {
    try {
      const reservasPendientes =
        await this.offlineStorage.getReservasOfflinePendientes(empresaId);
      const reserva = reservasPendientes.find((r: any) => r.uuid === reservaUuid);
      return reserva || null;
    } catch (error) {
      console.error(
        `[CU11] Error obteniendo reserva por UUID ${reservaUuid}:`,
        error,
      );
      return null;
    }
  }

  /**
   * Obtener una venta específica por UUID desde IndexedDB.
   *
   * Las ventas se indexan por empresa_id, por lo que iteramos
   * sobre las pendientes para encontrar la correcta.
   */
  private async obtenerVentaPorUuid(
    ventaUuid: string,
    empresaId: number,
  ): Promise<any | null> {
    try {
      const ventasPendientes =
        await this.offlineStorage.obtenerVentasOfflinePendientes(empresaId);
      const venta = ventasPendientes.find((v: any) => v.uuid === ventaUuid);
      return venta || null;
    } catch (error) {
      console.error(
        `[CU11] Error obteniendo venta por UUID ${ventaUuid}:`,
        error,
      );
      return null;
    }
  }

  /**
   * Obtener pago en efectivo asociado a una venta.
   */
  private async obtenerPagoVenta(ventaUuid: string): Promise<any | null> {
    try {
      return await this.offlineStorage.obtenerPagoVenta(ventaUuid);
    } catch (error) {
      console.error(
        `[CU11] Error obteniendo pago para venta ${ventaUuid}:`,
        error,
      );
      return null;
    }
  }

  /**
   * Sincronizar todas las operaciones pendientes (ventas + reservas).
   *
   * Esta es la función principal que debería dispararse
   * cuando FastAPI vuelve a estar disponible.
   */
  async sincronizarTodasLasOperaciones(): Promise<ResultadoSincronizacion[]> {
    const usuario = this.auth.usuario();
    if (!usuario?.empresa_id) {
      console.error('[CU11] Usuario no autenticado');
      return [];
    }

    const resultados: ResultadoSincronizacion[] = [];

    // Sincronizar ventas
    const ventasPendientes = await this.obtenerVentasPendientes(
      usuario.empresa_id,
    );
    for (const venta of ventasPendientes) {
      const resultado = await this.sincronizarVentaOffline(
        venta.uuid,
        usuario.empresa_id,
      );
      resultados.push(resultado);
    }

    // Sincronizar reservas
    const reservasPendientes = await this.obtenerReservasPendientes(
      usuario.empresa_id,
    );
    for (const reserva of reservasPendientes) {
      const resultado = await this.sincronizarReservaOffline(
        reserva.uuid,
        usuario.empresa_id,
      );
      resultados.push(resultado);
    }

    console.log(`[CU11] Sincronización completada: ${resultados.length} operaciones`);
    return resultados;
  }
}
