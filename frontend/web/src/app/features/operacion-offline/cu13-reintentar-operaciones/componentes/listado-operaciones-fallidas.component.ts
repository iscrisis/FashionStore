import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { AuthService } from '../../../../core/services/auth.service';
import { OfflineStorageService } from '../../../../core/services/offline-storage.service';
import { ReintentoOperacionesService } from '../servicios/reintentar-operaciones.service';
import { OperacionFallida, ResultadoReintento } from '../modelos/operacion-fallida.model';

@Component({
  selector: 'app-listado-operaciones-fallidas',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container">
      <h2>Operaciones Offline Fallidas</h2>

      <div *ngIf="cargando" class="alert alert-info">
        Cargando operaciones fallidas...
      </div>

      <div *ngIf="!cargando && operacionesFallidas.length === 0" class="alert alert-success">
        ✓ No hay operaciones fallidas. Todas las operaciones están sincronizadas.
      </div>

      <div *ngIf="operacionesFallidas.length > 0" class="listado">
        <div *ngFor="let op of operacionesFallidas" class="operacion-card">
          <div class="operacion-header">
            <span class="tipo-badge" [ngClass]="{ venta: op.tipo_operacion === 'VENTA_OFFLINE', reserva: op.tipo_operacion === 'RESERVA_OFFLINE' }">
              {{ op.tipo_operacion === 'VENTA_OFFLINE' ? 'Venta' : 'Reserva' }}
            </span>
            <span class="estado-badge" [ngClass]="{ rechazada: op.estado === 'RECHAZADA', conflicto: op.estado === 'CONFLICTO' }">
              {{ op.estado }}
            </span>
            <span class="uuid-text">{{ op.uuid }}</span>
          </div>

          <div class="operacion-body">
            <div *ngIf="op.motivo" class="motivo">
              <strong>Motivo:</strong> {{ op.motivo }}
            </div>
            <div class="intentos">
              <strong>Intentos:</strong> {{ op.numero_intentos }}/5
            </div>
            <div class="ultima-fecha">
              <strong>Último intento:</strong> {{ op.ultima_fecha_intento | date: 'short' }}
            </div>
            <div class="proximo-reintento">
              <strong>Disponible:</strong>
              <span *ngIf="reintentoDisponible(op)" class="disponible">Ahora</span>
              <span *ngIf="!reintentoDisponible(op)" class="espera">
                En {{ formatearTiempo(op.proximo_reintento_disponible_en_ms) }}
              </span>
            </div>
          </div>

          <div class="operacion-actions">
            <button
              *ngIf="reintentoDisponible(op)"
              class="btn btn-primary"
              (click)="reintentar(op)"
              [disabled]="reintentandoUuid === op.uuid"
            >
              {{ reintentandoUuid === op.uuid ? 'Reintentando...' : 'Reintentar Ahora' }}
            </button>
            <button
              *ngIf="!reintentoDisponible(op)"
              class="btn btn-secondary"
              disabled
            >
              Esperar {{ formatearTiempo(op.proximo_reintento_disponible_en_ms) }}
            </button>
          </div>
        </div>
      </div>

      <div *ngIf="ultimoResultado" [ngClass]="{ 'alert': true, 'alert-success': ultimoResultado.estado === 'CONFIRMADA', 'alert-warning': ultimoResultado.estado === 'RECHAZADA', 'alert-danger': ultimoResultado.estado === 'CONFLICTO' }">
        <strong>Resultado:</strong> {{ ultimoResultado.estado }}
        <span *ngIf="ultimoResultado.motivo">— {{ ultimoResultado.motivo }}</span>
        <span *ngIf="ultimoResultado.estado === 'CONFIRMADA'">
          <span *ngIf="ultimoResultado.venta_id">(Venta #{{ ultimoResultado.venta_id }})</span>
          <span *ngIf="ultimoResultado.reserva_id">(Reserva #{{ ultimoResultado.reserva_id }})</span>
        </span>
      </div>
    </div>
  `,
  styles: [`
    .container {
      padding: 20px;
    }

    h2 {
      margin-bottom: 20px;
      color: #333;
    }

    .alert {
      padding: 12px;
      margin-bottom: 20px;
      border-radius: 4px;
    }

    .alert-info {
      background-color: #d1ecf1;
      color: #0c5460;
    }

    .alert-success {
      background-color: #d4edda;
      color: #155724;
    }

    .alert-warning {
      background-color: #fff3cd;
      color: #856404;
    }

    .alert-danger {
      background-color: #f8d7da;
      color: #721c24;
    }

    .listado {
      display: grid;
      gap: 15px;
    }

    .operacion-card {
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 15px;
      background-color: #f9f9f9;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .operacion-header {
      display: flex;
      gap: 10px;
      align-items: center;
      padding-bottom: 10px;
      border-bottom: 1px solid #eee;
    }

    .tipo-badge {
      padding: 4px 8px;
      border-radius: 3px;
      font-size: 12px;
      font-weight: bold;
      color: white;
    }

    .tipo-badge.venta {
      background-color: #007bff;
    }

    .tipo-badge.reserva {
      background-color: #28a745;
    }

    .estado-badge {
      padding: 4px 8px;
      border-radius: 3px;
      font-size: 12px;
      font-weight: bold;
      color: white;
    }

    .estado-badge.rechazada {
      background-color: #dc3545;
    }

    .estado-badge.conflicto {
      background-color: #fd7e14;
    }

    .uuid-text {
      font-family: monospace;
      font-size: 12px;
      color: #666;
      flex: 1;
      text-align: right;
    }

    .operacion-body {
      display: grid;
      gap: 8px;
      font-size: 14px;
    }

    .motivo {
      color: #856404;
      background-color: #fff3cd;
      padding: 8px;
      border-radius: 3px;
    }

    .disponible {
      color: #28a745;
      font-weight: bold;
    }

    .espera {
      color: #fd7e14;
      font-weight: bold;
    }

    .operacion-actions {
      display: flex;
      gap: 10px;
    }

    .btn {
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      font-weight: bold;
      transition: background-color 0.2s;
    }

    .btn-primary {
      background-color: #007bff;
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      background-color: #0056b3;
    }

    .btn-secondary {
      background-color: #6c757d;
      color: white;
    }

    .btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  `]
})
export class ListadoOperacionesFallidasComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly offlineStorage = inject(OfflineStorageService);
  private readonly reintento = inject(ReintentoOperacionesService);

  operacionesFallidas: OperacionFallida[] = [];
  cargando = false;
  reintentandoUuid: string | null = null;
  ultimoResultado: ResultadoReintento | null = null;

  async ngOnInit(): Promise<void> {
    await this.cargarOperacionesFallidas();
  }

  async cargarOperacionesFallidas(): Promise<void> {
    this.cargando = true;
    const usuario = this.auth.usuario();

    if (!usuario?.empresa_id) {
      console.error('[CU13] Usuario no autenticado');
      this.cargando = false;
      return;
    }

    try {
      const ventasRechazadas = await this.offlineStorage.obtenerVentasOfflineRechazadas(usuario.empresa_id);
      const reservasRechazadas = await this.offlineStorage.getReservasOfflineRechazadas(usuario.empresa_id);

      // Convertir a OperacionFallida
      this.operacionesFallidas = [
        ...ventasRechazadas.map((v: any) => ({
          uuid: v.uuid,
          tipo_operacion: 'VENTA_OFFLINE' as const,
          estado: v.estado_sync as 'RECHAZADA' | 'CONFLICTO',
          motivo: v.motivo_rechazo,
          numero_intentos: v.numero_intentos || 1,
          ultima_fecha_intento: v.fecha_sincronizacion || new Date().toISOString(),
          proximo_reintento_disponible_en_ms: v.proximo_reintento_ms || 0,
        })),
        ...reservasRechazadas.map((r: any) => ({
          uuid: r.uuid,
          tipo_operacion: 'RESERVA_OFFLINE' as const,
          estado: r.estado_sync as 'RECHAZADA' | 'CONFLICTO',
          motivo: r.motivo_rechazo,
          numero_intentos: r.numero_intentos || 1,
          ultima_fecha_intento: r.fecha_sincronizacion || new Date().toISOString(),
          proximo_reintento_disponible_en_ms: r.proximo_reintento_ms || 0,
        })),
      ];

      console.log(`[CU13] Cargadas ${this.operacionesFallidas.length} operaciones fallidas`);
    } catch (error) {
      console.error('[CU13] Error cargando operaciones fallidas:', error);
    } finally {
      this.cargando = false;
    }
  }

  reintentoDisponible(op: OperacionFallida): boolean {
    return this.reintento.esElegibleParaReintento(op);
  }

  formatearTiempo(ms: number): string {
    return this.reintento.formatearTiempoEspera(ms);
  }

  async reintentar(op: OperacionFallida): Promise<void> {
    const usuario = this.auth.usuario();
    if (!usuario?.empresa_id) return;

    this.reintentandoUuid = op.uuid;

    try {
      let resultado: ResultadoReintento;

      if (op.tipo_operacion === 'VENTA_OFFLINE') {
        resultado = await this.reintento.reintentoVenta(op.uuid, usuario.empresa_id);
      } else {
        resultado = await this.reintento.reintentoReserva(op.uuid, usuario.empresa_id);
      }

      this.ultimoResultado = resultado;

      // Recargar lista después de un pequeño delay
      setTimeout(() => this.cargarOperacionesFallidas(), 1000);
    } catch (error) {
      console.error('[CU13] Error durante reintento:', error);
      this.ultimoResultado = {
        uuid_local: op.uuid,
        tipo_operacion: op.tipo_operacion,
        estado: 'RECHAZADA',
        motivo: 'Error durante reintento',
        numero_intento: op.numero_intentos,
        proximo_reintento_en_ms: 30000,
      };
    } finally {
      this.reintentandoUuid = null;
    }
  }
}
