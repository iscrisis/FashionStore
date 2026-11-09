import { Injectable, OnDestroy, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, Subject, timeout } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ConnectivityService implements OnDestroy {
  private http = inject(HttpClient);
  private isOnlineSubject = new BehaviorSubject<boolean>(navigator.onLine);
  isOnline$: Observable<boolean> = this.isOnlineSubject.asObservable();

  private destroy$ = new Subject<void>();
  private lastCheckTime = 0;
  private checkDebounceMs = 2000; // 2 segundos entre comprobaciones
  private healthCheckTimeoutMs = 3000; // 3 segundos timeout para health check
  private isCheckingHealth = false;
  private healthCheckUrl = `${environment.apiUrl}/health`;

  // Sondeo periódico de FastAPI
  private periodicCheckInterval: any = null;
  private readonly periodicCheckIntervalMs = 5000; // 5 segundos
  private isAppVisible = true;

  constructor() {
    console.log(`%c[CONNECTIVITY] VERSIÓN CORREGIDA 2026-11-09 — Usando health check real + sondeo periódico + navigator.onLine`, 'background:green;color:white;font-weight:bold');
    console.log(`%c[CONNECTIVITY] Health check endpoint: ${this.healthCheckUrl}`, 'background:blue;color:white');
    console.log(`%c[CONNECTIVITY] Sondeo periódico: cada ${this.periodicCheckIntervalMs}ms cuando app está visible`, 'background:blue;color:white');

    this.setupListeners();
    this.checkConnectivityOnInit();
    this.setupVisibilityListener();
    this.startPeriodicHealthCheck();
  }

  private setupListeners(): void {
    window.addEventListener('online', () => {
      console.log('✓ Evento online detectado — verificando backend...');
      this.verifyBackendAvailability();
    });

    window.addEventListener('offline', () => {
      console.log('✗ Evento offline detectado — cambiar a modo offline');
      this.isOnlineSubject.next(false);
    });
  }

  private checkConnectivityOnInit(): void {
    setTimeout(() => {
      console.log('[CONNECTIVITY] Verificación inicial al iniciar la aplicación');
      this.verifyBackendAvailability();
    }, 500);
  }

  private setupVisibilityListener(): void {
    document.addEventListener('visibilitychange', () => {
      this.isAppVisible = !document.hidden;

      if (this.isAppVisible) {
        console.log('[CONNECTIVITY] Aplicación recuperada — revalidar conectividad');
        // Reanudar sondeo periódico
        this.startPeriodicHealthCheck();
        // Verificación inmediata
        this.verifyBackendAvailability();
      } else {
        console.log('[CONNECTIVITY] Aplicación en segundo plano — pausar sondeo periódico');
        // Pausar sondeo periódico mientras está en fondo
        this.stopPeriodicHealthCheck();
      }
    });
  }

  private startPeriodicHealthCheck(): void {
    // No iniciar múltiples intervalos
    if (this.periodicCheckInterval) {
      return;
    }

    console.log('[CONNECTIVITY] Iniciando sondeo periódico de FastAPI');
    this.periodicCheckInterval = setInterval(() => {
      // Solo hacer sondeo si la app está visible
      if (this.isAppVisible) {
        this.verifyBackendAvailability();
      }
    }, this.periodicCheckIntervalMs);
  }

  private stopPeriodicHealthCheck(): void {
    if (this.periodicCheckInterval) {
      console.log('[CONNECTIVITY] Deteniendo sondeo periódico');
      clearInterval(this.periodicCheckInterval);
      this.periodicCheckInterval = null;
    }
  }

  private verifyBackendAvailability(): void {
    // Evitar verificaciones simultáneas
    if (this.isCheckingHealth) {
      console.log('[CONNECTIVITY] Ya hay una verificación en curso — ignorar');
      return;
    }

    // Evitar comprobaciones muy frecuentes
    const now = Date.now();
    if (now - this.lastCheckTime < this.checkDebounceMs) {
      console.log('[CONNECTIVITY] Última comprobación muy reciente — ignorar');
      return;
    }

    this.lastCheckTime = now;
    this.isCheckingHealth = true;

    // Health check con timeout y evitar caché
    this.http
      .get<{ status: string }>(this.healthCheckUrl, {
        headers: { 'Cache-Control': 'no-cache, no-store' }
      })
      .pipe(
        timeout(this.healthCheckTimeoutMs),
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: (response) => {
          if (response.status === 'ok') {
            console.log('✓ Backend disponible (health check OK)');
            this.isOnlineSubject.next(true);
          } else {
            console.log('✗ Backend respondió pero estado no es OK');
            this.isOnlineSubject.next(false);
          }
          this.isCheckingHealth = false;
        },
        error: (err) => {
          console.log('✗ Backend no disponible (error en health check)', err.status);
          this.isOnlineSubject.next(false);
          this.isCheckingHealth = false;
        },
      });
  }

  isOnline(): boolean {
    // Retornar el estado actual del BehaviorSubject que se actualiza con health checks
    const online = this.isOnlineSubject.value;
    const navigatorOnline = navigator.onLine;

    console.log(`[CONNECTIVITY] navigator.onLine=${navigatorOnline} | health_check=${online} | returning=${online}`);

    // Si navigator dice offline, respetar eso
    if (!navigatorOnline) {
      console.log('[CONNECTIVITY] navigator.onLine=false — forzar offline');
      if (online !== false) {
        this.isOnlineSubject.next(false);
      }
      return false;
    }

    // Confiar en el health check (mas confiable que navigator.onLine para Wi-Fi apagado)
    return online;
  }

  ngOnDestroy(): void {
    this.stopPeriodicHealthCheck();
    this.destroy$.next();
    this.destroy$.complete();
  }
}
