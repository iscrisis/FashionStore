import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, from } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ConnectivityService } from '../../core/services/connectivity.service';
import { AuthService } from '../../core/services/auth.service';
import { OfflineStorageService } from '../../core/services/offline-storage.service';
import { ConsultaOperacionesLocalesService } from '../operacion-offline/cu10-consultar-datos-operaciones-locales/consulta-operaciones-locales.service';
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
  private readonly connectivity = inject(ConnectivityService);
  private readonly auth = inject(AuthService);
  private readonly offlineStorage = inject(OfflineStorageService);
  private readonly cu10 = inject(ConsultaOperacionesLocalesService);
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
    const isOnline = this.connectivity.isOnline();

    if (!isOnline) {
      // CU27 — Offline: obtener historial confirmado + pendientes desde IndexedDB
      return from(this.listarMiasOffline(filtro));
    }

    // Online: obtener del backend y guardar localmente
    return new Observable((observer) => {
      this.http
        .get<VentaHistorialOut[]>(`${this.baseUrl}/mias`, { params: this.construirParams(filtro) })
        .subscribe({
          next: async (compras) => {
            try {
              const usuario = this.auth.usuario();
              const empresaId = usuario?.empresa_id || 1;
              const clienteId = usuario?.id || 0;

              // Guardar localmente para consulta offline (CLIENTE: con clienteId)
              await this.offlineStorage.guardarHistorialConfirmado(compras, empresaId, clienteId);
              observer.next(compras);
            } catch (error) {
              console.error('[CU27] Error al guardar historial local:', error);
              observer.next(compras); // Retornar datos aunque falle guardado local
            }
            observer.complete();
          },
          error: (err) => observer.error(err),
        });
    });
  }

  // CU27 — Obtener historial offline (confirmado + pendientes)
  private async listarMiasOffline(filtro: FiltroHistorial): Promise<VentaHistorialOut[]> {
    try {
      const usuario = this.auth.usuario();
      const empresaId = usuario?.empresa_id || 1;
      const clienteId = usuario?.id || 0;

      // Obtener historial confirmado del cliente (CLIENTE: con clienteId)
      const historialConfirmado = await this.offlineStorage.obtenerHistorialConfirmado(empresaId, clienteId);

      // Obtener ventas pendientes de sincronización
      const ventasPendientes = await this.cu10.consultarVentasOffline(empresaId);
      const ventasPendientesCliente = ventasPendientes.filter((v: any) => v.cliente_id === clienteId || !v.cliente_id);

      // Combinar: confirmadas + pendientes
      const combinadas: VentaHistorialOut[] = [
        ...historialConfirmado.map((v: any) => ({
          venta_id: v.venta_id,
          codigo_venta: v.codigo_venta,
          fecha: v.fecha,
          sucursal: { id: v.sucursal_id, nombre: 'Sucursal', ciudad: 'Local' },
          cliente_nombre: usuario?.nombre || 'Cliente',
          tipo: v.tipo,
          metodo_pago: v.metodo_pago,
          total: v.total,
          tiene_postventa: v.tiene_postventa,
          leyenda_postventa: v.leyenda_postventa,
        })),
        ...ventasPendientesCliente.map((v: any) => ({
          venta_id: parseInt(v.uuid.slice(0, 8), 16) % 1000000,
          codigo_venta: `LOC-${v.uuid.slice(0, 8).toUpperCase()}`,
          fecha: v.fecha_creacion,
          sucursal: { id: v.sucursal_id, nombre: 'Sucursal Local', ciudad: 'Local' },
          cliente_nombre: usuario?.nombre || 'Cliente',
          tipo: v.tipo || 'PRESENCIAL',
          metodo_pago: v.metodo_pago || 'EFECTIVO',
          total: v.total,
          tiene_postventa: false,
          leyenda_postventa: null,
        })),
      ];

      console.log('[CU27 OFFLINE] Historial combinado:', { confirmadas: historialConfirmado.length, pendientes: ventasPendientesCliente.length });
      return combinadas;
    } catch (error) {
      console.error('[CU27 OFFLINE] Error obteniendo historial offline:', error);
      return [];
    }
  }

  listarSucursal(filtro: FiltroHistorial): Observable<VentaHistorialOut[]> {
    const isOnline = this.connectivity.isOnline();

    if (!isOnline) {
      // CU27 — Offline: obtener historial confirmado + pendientes desde IndexedDB
      return from(this.listarSucursalOffline(filtro));
    }

    // Online: obtener del backend y guardar localmente
    return new Observable((observer) => {
      this.http
        .get<VentaHistorialOut[]>(`${this.baseUrl}/sucursal`, {
          params: this.construirParams(filtro),
        })
        .subscribe({
          next: async (ventas) => {
            try {
              const usuario = this.auth.usuario();
              const empresaId = usuario?.empresa_id || 1;

              // Obtener sucursal_id del contexto autenticado (preparaciones locales del CAJERO)
              const preparaciones = await this.offlineStorage.getAllPreparaciones(empresaId).catch(() => []);
              const sucursalId = preparaciones?.length > 0 ? preparaciones[0]?.metadata?.sucursal_id : undefined;

              // Guardar localmente para consulta offline (CAJERO: con sucursalId)
              await this.offlineStorage.guardarHistorialConfirmado(ventas, empresaId, undefined, sucursalId);
              observer.next(ventas);
            } catch (error) {
              console.error('[CU27 CAJERO] Error al guardar historial local:', error);
              observer.next(ventas); // Retornar datos aunque falle guardado local
            }
            observer.complete();
          },
          error: (err) => observer.error(err),
        });
    });
  }

  // CU27 — Obtener ventas offline de sucursal (historial confirmado + pendientes)
  private async listarSucursalOffline(filtro: FiltroHistorial): Promise<VentaHistorialOut[]> {
    try {
      const usuario = this.auth.usuario();
      const empresaId = usuario?.empresa_id || 1;

      // 1. Obtener sucursal_id del contexto autenticado
      const preparaciones = await this.offlineStorage.getAllPreparaciones(empresaId).catch(() => []);
      const sucursalId = preparaciones?.length > 0 ? preparaciones[0]?.metadata?.sucursal_id : undefined;

      // 2. Obtener historial confirmado de la sucursal
      const historialConfirmado = sucursalId
        ? await this.offlineStorage.obtenerHistorialConfirmadoPorSucursal(empresaId, sucursalId)
        : [];

      // 3. Obtener ventas pendientes de sincronización
      const ventasOffline = await this.cu10.consultarVentasOffline(empresaId);

      // 4. Mapear historial confirmado
      const historialMapeado: VentaHistorialOut[] = historialConfirmado.map((v: any) => ({
        venta_id: v.venta_id,
        codigo_venta: v.codigo_venta,
        fecha: v.fecha,
        sucursal: { id: v.sucursal_id, nombre: 'Sucursal', ciudad: 'Local' },
        cliente_nombre: v.cliente_nombre || null,
        tipo: v.tipo,
        metodo_pago: v.metodo_pago,
        total: v.total,
        tiene_postventa: v.tiene_postventa,
        leyenda_postventa: v.leyenda_postventa,
      }));

      // 5. Mapear ventas pendientes (CU10 ya retorna VentaOfflineCompleta con datos mapeados)
      const ventasPendientesMapeadas: VentaHistorialOut[] = ventasOffline.map((v: any) => ({
        venta_id: v.venta_id,  // ← Ya calculado por CU10
        codigo_venta: v.codigo_venta,  // ← Ya generado por CU10
        fecha: v.fecha,
        sucursal: v.sucursal,
        cliente_nombre: v.cliente_nombre,
        tipo: v.tipo,
        metodo_pago: v.metodo_pago,
        total: v.total,
        tiene_postventa: v.tiene_postventa,
        leyenda_postventa: v.leyenda_postventa,
      }));

      // 6. Combinar: historial confirmado + pendientes
      const combinadas: VentaHistorialOut[] = [
        ...historialMapeado,
        ...ventasPendientesMapeadas,
      ];

      console.log('[CU27 OFFLINE] Historial combinado:', {
        confirmadas: historialMapeado.length,
        pendientes: ventasPendientesMapeadas.length,
        total: combinadas.length,
      });

      return combinadas;
    } catch (error) {
      console.error('[CU10 HISTORIAL] Error al consultar ventas offline:', error);
      return [];
    }
  }
}
