import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ConsultarResultadoSincronizacionService } from '../servicios/consultar-resultado-sincronizacion.service';
import {
  ResultadoSincronizacion,
  ResumenResultados,
} from '../modelos/resultado-sincronizacion.model';
import { OfflineStorageService } from '../../../../core/services/offline-storage.service';
import { AuthService } from '../../../../core/services/auth.service';

/**CU12 — Componente de resultados de sincronización.*/
@Component({
  selector: 'app-resultados-sincronizacion',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="container">
      <h2>Resultados de Sincronización</h2>

      <!-- Resumen -->
      <div class="resumen" *ngIf="resumen">
        <div class="stat">
          <span class="label">Confirmadas:</span>
          <span class="value">{{ resumen.confirmadas }}</span>
        </div>
        <div class="stat">
          <span class="label">Rechazadas:</span>
          <span class="value">{{ resumen.rechazadas }}</span>
        </div>
        <div class="stat">
          <span class="label">Conflictos:</span>
          <span class="value">{{ resumen.conflictos }}</span>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button
          [class.active]="tab === 'ventas'"
          (click)="tab = 'ventas'"
        >
          Ventas
        </button>
        <button
          [class.active]="tab === 'reservas'"
          (click)="tab = 'reservas'"
        >
          Reservas
        </button>
      </div>

      <!-- Listado de ventas -->
      <div *ngIf="tab === 'ventas'">
        <table>
          <thead>
            <tr>
              <th>UUID</th>
              <th>Código</th>
              <th>Total</th>
              <th>Fecha</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let venta of ventas">
              <td class="uuid">{{ venta.uuid_local | slice: 0: 8 }}...</td>
              <td>{{ venta.codigo_venta }}</td>
              <td>{{ venta.total | currency }}</td>
              <td>{{ venta.fecha_local | date: 'short' }}</td>
              <td class="estado">{{ venta.estado }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Listado de reservas -->
      <div *ngIf="tab === 'reservas'">
        <table>
          <thead>
            <tr>
              <th>UUID</th>
              <th>Código</th>
              <th>Fecha</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let reserva of reservas">
              <td class="uuid">{{ reserva.uuid_local | slice: 0: 8 }}...</td>
              <td>{{ reserva.codigo_reserva }}</td>
              <td>{{ reserva.fecha_local | date: 'short' }}</td>
              <td class="estado">{{ reserva.estado }}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  `,
  styles: [`
    .container { padding: 20px; }
    h2 { margin-bottom: 20px; }
    .resumen { display: flex; gap: 20px; margin-bottom: 20px; }
    .stat { display: flex; flex-direction: column; }
    .label { font-size: 0.9rem; color: #666; }
    .value { font-size: 1.5rem; font-weight: bold; }
    .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
    button { padding: 8px 16px; border: 1px solid #ddd; cursor: pointer; }
    button.active { background: #007bff; color: white; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
    .uuid { font-family: monospace; font-size: 0.85rem; }
    .estado { font-weight: bold; }
    .offline-notice { padding: 12px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; }
  `],
})
export class ResultadosSincronizacionComponent implements OnInit {
  private readonly service = inject(ConsultarResultadoSincronizacionService);
  private readonly offlineStorage = inject(OfflineStorageService);
  private readonly auth = inject(AuthService);

  tab: 'ventas' | 'reservas' = 'ventas';
  ventas: ResultadoSincronizacion[] = [];
  reservas: ResultadoSincronizacion[] = [];
  resumen: ResumenResultados | null = null;

  ngOnInit() {
    // Intentar cargar desde servidor; si falla, usar IndexedDB
    this.cargarDesdeServidor();
  }

  private cargarDesdeServidor() {
    this.service.listarResultadosVentas().subscribe({
      next: (v) => (this.ventas = v),
      error: () => this.cargarDesdeLocal(),
    });

    this.service.listarResultadosReservas().subscribe({
      next: (r) => (this.reservas = r),
      error: () => this.cargarDesdeLocal(),
    });

    this.service.obtenerResumen().subscribe({
      next: (r) => (this.resumen = r),
    });
  }

  private async cargarDesdeLocal() {
    const usuario = this.auth.usuario();
    if (!usuario?.empresa_id) {
      console.warn('[CU12] Usuario no autenticado, no hay datos locales');
      return;
    }

    try {
      // CU12 consulta resultados de sincronización desde operaciones offline
      const ventasLocales = await this.offlineStorage.obtenerVentasOfflinePendientes(
        usuario.empresa_id
      );
      const reservasLocales = await this.offlineStorage.getReservasOfflinePendientes(
        usuario.empresa_id
      );

      // Convertir operaciones locales a resultados de CU12
      // Nota: CU12 solo muestra operaciones que YA FUERON INTENTADO sincronizar
      // (estado_sync !== PENDIENTE_SYNC)
      const ventasConvertidas = await Promise.all(
        ventasLocales.map((v) => this.convertirVentaAResultado(v, usuario.id))
      );
      this.ventas = ventasConvertidas.filter((v) => v !== null) as ResultadoSincronizacion[];

      const reservasConvertidas = await Promise.all(
        reservasLocales.map((r) => this.convertirReservaAResultado(r, usuario.id))
      );
      this.reservas = reservasConvertidas.filter((r) => r !== null) as ResultadoSincronizacion[];

      this.calcularResumen();
      console.log('[CU12] Resultados cargados desde IndexedDB (sin conexión)');
    } catch (error) {
      console.error('[CU12] Error cargando resultados locales:', error);
    }
  }

  private async convertirVentaAResultado(
    venta: any,
    usuarioId: number
  ): Promise<ResultadoSincronizacion | null> {
    // CU12 solo muestra operaciones que YA FUE INTENTADO sincronizar
    // Si estado_sync === PENDIENTE_SYNC, aún no se sincronizó, no mostrar en CU12
    if (venta.estado_sync === 'PENDIENTE_SYNC') {
      return null;
    }

    return {
      uuid_local: venta.uuid,
      tipo_operacion: 'VENTA_OFFLINE',
      estado: venta.estado_sync === 'SINCRONIZADA' ? 'CONFIRMADA' : 'RECHAZADA',
      motivo: venta.motivo_rechazo || null,
      venta_id: venta.id || null,
      codigo_venta: venta.codigo_venta || null,
      reserva_id: null,
      codigo_reserva: null,
      fecha_local: venta.fecha_creacion,
      fecha_sincronizacion: null,
      total: venta.total,
      empresa_id: venta.empresa_id,
      sucursal_id: venta.sucursal_id,
    };
  }

  private async convertirReservaAResultado(
    reserva: any,
    usuarioId: number
  ): Promise<ResultadoSincronizacion | null> {
    // Filtro: cliente debe ser el dueño de la reserva
    if (reserva.cliente_id && reserva.cliente_id !== usuarioId) {
      return null;
    }

    // CU12 solo muestra operaciones que YA FUERON INTENTADO sincronizar
    if (reserva.estado_sync === 'PENDIENTE_SYNC') {
      return null;
    }

    return {
      uuid_local: reserva.uuid,
      tipo_operacion: 'RESERVA_OFFLINE',
      estado: reserva.estado_sync === 'SINCRONIZADA' ? 'CONFIRMADA' : 'RECHAZADA',
      motivo: reserva.motivo_rechazo || null,
      venta_id: null,
      codigo_venta: null,
      reserva_id: reserva.id || null,
      codigo_reserva: reserva.codigo_reserva || null,
      fecha_local: reserva.fecha_creacion,
      fecha_sincronizacion: null,
      total: null,
      empresa_id: reserva.empresa_id,
      sucursal_id: reserva.sucursal_id,
    };
  }

  private calcularResumen() {
    const todos = [...this.ventas, ...this.reservas].filter((r) => r !== null);
    this.resumen = {
      confirmadas: todos.filter((r) => r.estado === 'CONFIRMADA').length,
      pendientes: 0,
      rechazadas: todos.filter((r) => r.estado === 'RECHAZADA').length,
      conflictos: todos.filter((r) => r.estado === 'CONFLICTO').length,
      total: todos.length,
    };
  }
}
