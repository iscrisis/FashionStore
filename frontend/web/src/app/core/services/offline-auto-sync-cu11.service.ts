import { Injectable, inject } from '@angular/core';
import { AuthService } from './auth.service';
import { ConnectivityService } from './connectivity.service';
import { SincronizarOperacionesPendientesService } from '../../features/operacion-offline/cu11-sincronizar-operaciones-pendientes/servicios/sincronizar-operaciones-pendientes.service';
import { OfflineStorageService } from './offline-storage.service';

/**
 * CU11 — Sincronización automática de operaciones offline.
 *
 * Se dispara automáticamente cuando:
 * - Usuario está autenticado
 * - Conexión a FastAPI se recupera (cambio de false a true en ConnectivityService.isOnline$)
 * - Hay operaciones pendientes en IndexedDB
 *
 * NO espera intervención del usuario ni requiere botones.
 * Respeta sesión, empresa, sucursal, cliente y usuario.
 * Evita sincronizaciones simultáneas.
 */
@Injectable({
  providedIn: 'root',
})
export class OfflineAutoSyncCU11Service {
  private readonly authService = inject(AuthService);
  private readonly connectivity = inject(ConnectivityService);
  private readonly sincronizar = inject(SincronizarOperacionesPendientesService);
  private readonly offlineStorage = inject(OfflineStorageService);

  private syncInProgress = false;
  private lastSyncTime = 0;
  private readonly syncDebounceMs = 3000; // Esperar 3s entre sincronizaciones
  private configurationErrorDetected = false; // Bloqueo temporal por error 404
  private lastErrorTime = 0;
  private readonly errorRecoveryDelayMs = 60000; // 1 minuto antes de reintentar tras 404

  /**
   * Inicializar el listener automático de cambios de conectividad.
   * Se llama una vez desde app.ts.
   */
  iniciarListenerAutomatico(): void {
    console.log('[CU11 AUTO-SYNC] Inicializando listener automático de conectividad');

    // Escuchar cambios de conectividad desde ConnectivityService
    this.connectivity.isOnline$.subscribe(async (isOnline) => {
      console.log(`[CU11 AUTO-SYNC] Cambio de conectividad detectado: ${isOnline}`);

      if (isOnline) {
        // Conectividad recuperada: ejecutar sincronización automática
        // PERO: si hay un error de configuración (404), esperar a recuperación
        if (this.configurationErrorDetected) {
          const timeSinceError = Date.now() - this.lastErrorTime;
          if (timeSinceError < this.errorRecoveryDelayMs) {
            console.log(
              `[CU11 AUTO-SYNC] Error de configuración detectado. ` +
              `Esperando ${this.errorRecoveryDelayMs - timeSinceError}ms antes de reintentar.`
            );
            return;
          }
          console.log('[CU11 AUTO-SYNC] Reintentando tras error de configuración...');
          this.configurationErrorDetected = false;
        }

        await this.sincronizarAutomaticamente();
      }
    });
  }

  /**
   * Ejecutar sincronización automática con protecciones.
   */
  private async sincronizarAutomaticamente(): Promise<void> {
    const usuario = this.authService.usuario();

    // Validación: usuario autenticado
    if (!usuario?.empresa_id) {
      console.log('[CU11 AUTO-SYNC] Usuario no autenticado, saltar sincronización');
      return;
    }

    // Validación: no hay otra sincronización en progreso
    if (this.syncInProgress) {
      console.log('[CU11 AUTO-SYNC] Sincronización ya en progreso, saltar');
      return;
    }

    // Validación: no sincronizar muy frecuentemente
    const now = Date.now();
    if (now - this.lastSyncTime < this.syncDebounceMs) {
      console.log('[CU11 AUTO-SYNC] Última sincronización muy reciente, saltar');
      return;
    }

    this.syncInProgress = true;
    this.lastSyncTime = now;

    try {
      console.log(`[CU11 AUTO-SYNC] Iniciando sincronización automática para empresa ${usuario.empresa_id}`);

      // Obtener operaciones pendientes
      const ventasPendientes = await this.offlineStorage.obtenerVentasOfflinePendientes(usuario.empresa_id);
      const reservasPendientes = await this.offlineStorage.getReservasOfflinePendientes(usuario.empresa_id);

      const totalPendientes = (ventasPendientes?.length || 0) + (reservasPendientes?.length || 0);

      if (totalPendientes === 0) {
        console.log('[CU11 AUTO-SYNC] No hay operaciones pendientes');
        return;
      }

      console.log(
        `[CU11 AUTO-SYNC] Encontradas ${totalPendientes} operaciones pendientes ` +
        `(${ventasPendientes?.length} ventas, ${reservasPendientes?.length} reservas)`
      );

      // Ejecutar sincronización (CU11 manejará los resultados)
      const resultados = await this.sincronizar.sincronizarTodasLasOperaciones();

      console.log(`[CU11 AUTO-SYNC] Sincronización completada: ${resultados.length} operaciones procesadas`);

      // Registrar resumen
      const confirmadas = resultados.filter((r) => r.estado === 'CONFIRMADA').length;
      const rechazadas = resultados.filter((r) => r.estado === 'RECHAZADA').length;
      const conflictos = resultados.filter((r) => r.estado === 'CONFLICTO').length;

      console.log(
        `[CU11 AUTO-SYNC] Resumen: ${confirmadas} confirmadas, ` +
        `${rechazadas} rechazadas, ${conflictos} conflictos`
      );
    } catch (error: any) {
      // Detectar error de configuración (404 = ruta no existe)
      if (error?.status === 404 || error?.statusCode === 404) {
        console.error(
          '[CU11 AUTO-SYNC] ❌ ERROR CRÍTICO: Endpoint de sincronización no encontrado (404). ' +
          'Esto indica que el backend no tiene la ruta CU11 registrada. ' +
          'Verificar: 1) Backend reconstruido, 2) main.py incluye router CU11, 3) OpenAPI actualizado.'
        );
        this.configurationErrorDetected = true;
        this.lastErrorTime = Date.now();
        // No reintentar hasta después del delay de recuperación
        console.log(
          `[CU11 AUTO-SYNC] Sincronización pausada por ${this.errorRecoveryDelayMs / 1000}s ` +
          `(error de configuración, no de conexión)`
        );
      } else {
        console.error('[CU11 AUTO-SYNC] Error durante sincronización automática:', error);
      }
      // Error no es crítico: conservar estado local, no romper aplicación
    } finally {
      this.syncInProgress = false;
    }
  }
}
