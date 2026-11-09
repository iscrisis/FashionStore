import { Component, inject, effect } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ToastContainer } from './core/ui/toast/toast-container';
import { ConfirmDialog } from './core/ui/confirm-dialog/confirm-dialog';
import { AuthService } from './core/services/auth.service';
import { OfflineAutoSyncService } from './core/services/offline-auto-sync.service';
import { OfflineAutoSyncCU11Service } from './core/services/offline-auto-sync-cu11.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, ToastContainer, ConfirmDialog],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly authService = inject(AuthService);
  private readonly offlineAutoSync = inject(OfflineAutoSyncService);
  private readonly offlineAutoSyncCU11 = inject(OfflineAutoSyncCU11Service);

  constructor() {
    // CU06 — Preparación automática de datos offline
    effect(() => {
      const usuario = this.authService.usuario();
      if (usuario?.empresa_id) {
        console.log('CU06: Iniciando preparación automática...');
        this.offlineAutoSync.prepararAutomaticamente().catch((error) => {
          console.warn('CU06: Error en preparación automática:', error);
        });
      }
    });

    // CU11 — Sincronización automática de operaciones offline
    // Se dispara cuando la conectividad cambia de offline a online
    this.offlineAutoSyncCU11.iniciarListenerAutomatico();
  }
}
