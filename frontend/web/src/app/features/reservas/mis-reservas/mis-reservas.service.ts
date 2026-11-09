import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, from, tap } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ReservaOut } from '../crear-reserva/crear-reserva.model';
import { ConsultaOperacionesLocalesService } from '../../../features/operacion-offline/cu10-consultar-datos-operaciones-locales/consulta-operaciones-locales.service';
import { OfflineStorageService } from '../../../core/services/offline-storage.service';
import { AuthService } from '../../../core/services/auth.service';

/** Consume CU18 -- Consultar reserva (Cliente). Reutiliza GET /reservas/mias,
 * el mismo endpoint que ya expone CU17 (ver backend
 * modules/P4_ReservasYAtencion/CU18_ConsultarReserva/__init__.py).
 * Delega consultas offline a CU10 y persiste historial en IndexedDB. */
@Injectable({ providedIn: 'root' })
export class MisReservasService {
  private readonly http = inject(HttpClient);
  private readonly cu10 = inject(ConsultaOperacionesLocalesService);
  private readonly offlineStorage = inject(OfflineStorageService);
  private readonly auth = inject(AuthService);
  private readonly baseUrl = `${environment.apiUrl}/reservas`;

  listarMias(): Observable<ReservaOut[]> {
    return this.http.get<ReservaOut[]>(`${this.baseUrl}/mias`).pipe(
      tap(async (reservas) => {
        // Guardar en IndexedDB para acceso offline
        const usuario = this.auth.usuario();
        if (usuario?.empresa_id) {
          await this.offlineStorage.guardarHistorialReservasConfirmado(
            reservas,
            usuario.empresa_id,
            usuario.id
          );
        }
      })
    );
  }

  listarMiasOffline(empresaId: number, clienteId: number): Observable<any[]> {
    return from(this.listarMiasOfflineAsync(empresaId, clienteId));
  }

  private async listarMiasOfflineAsync(empresaId: number, clienteId: number): Promise<any[]> {
    // Combinar historial descargado + reservas pendientes
    const [historialConfirmado, reservasPendientes] = await Promise.all([
      this.offlineStorage.obtenerHistorialReservasConfirmado(empresaId, clienteId),
      this.cu10.consultarReservasOfflineCompletas(empresaId, clienteId),
    ]);

    // Historial ya vienen formateadas de IndexedDB, reservas pendientes de CU10
    // No combinar detalles aquí — cada fuente retorna su estructura
    return [...historialConfirmado, ...reservasPendientes];
  }
}
