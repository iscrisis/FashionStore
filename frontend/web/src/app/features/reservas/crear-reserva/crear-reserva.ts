import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { formatearFechaReserva, formatearHorarioReserva } from '../reserva-formato';
import { ReservaOut } from './crear-reserva.model';
import { CrearReservaService } from './crear-reserva.service';
import { bloquesHorarioDisponibles, fechaMaximaIso, hoyIso, proximosDias } from './horario-reserva';
import { ConnectivityService } from '../../../core/services/connectivity.service';
import { OfflineStorageService } from '../../../core/services/offline-storage.service';
import { generarUUID } from '../../../core/utils/uuid';

/**
 * CU17 -- Crear reserva de prendas (Cliente), incluido agregar una prenda a
 * una reserva PENDIENTE ya existente en la misma sucursal.
 *
 * Botón fijo arriba de "Stock por sucursal" (ver producto-detalle.html) que
 * abre un modal una vez hay producto+variante+sucursal elegidos más abajo en
 * la misma ficha (producto-detalle.ts). Con sesión, antes de pedir fecha/
 * hora se consulta GET /reservas/compatibles (reservas PROPIAS, en esa
 * MISMA sucursal, todavía PENDIENTE -- ver service.ts):
 *  - si hay alguna, se muestra el modal "Tienes una reserva pendiente en
 *    esta sucursal" con cada una (código, sucursal, fecha, horario, cuántas
 *    prendas ya tiene) y dos salidas: "Agregar a esta reserva" (POST
 *    /reservas/{id}/detalles -- NUNCA crea una cabecera nueva) o "Programar
 *    otra visita" (sigue al modal de fecha/hora de siempre);
 *  - si no hay ninguna, se salta directo al modal de fecha/hora, exactamente
 *    como antes de este cambio.
 * Sin sesión, el flujo NO cambia: no hay cliente_id todavío con el que
 * consultar compatibles, así que se abre el modal de fecha/hora igual que
 * siempre y la sesión se verifica recién al confirmar.
 *
 * El modal NUNCA navega a otra pantalla ni pide sesión para abrirse o para
 * elegir fecha/hora -- eso sigue siendo público. La sesión se verifica
 * recién al presionar "Confirmar reserva" dentro del modal:
 *  - sin sesión: navega a /login con returnUrl (que ya conserva ciudad,
 *    sucursal, talla y color -- ver producto-detalle.ts -- más fecha/hora,
 *    que este componente agrega aquí mismo porque es quien las conoce).
 *  - con sesión: llama al POST /reservas existente, sin cambios de
 *    contrato.
 *
 * Al volver del login, si returnUrl traía fecha/hora válidas (dentro de la
 * ventana de 7 días, no domingo, bloque real para esa fecha), esa selección
 * se restaura y AHORA que ya hay sesión también se consulta compatibles --
 * el Cliente puede terminar agregando la prenda a una reserva existente en
 * vez de crear una nueva, incluso habiendo elegido fecha/hora antes de
 * loguearse.
 *
 * La confirmación de éxito usa el ToastService global con el tipo "brand"
 * (ver toast.service.ts): toast flotante, position fixed, acento rojo de
 * FashionStore -- no afecta el "success" verde que siguen usando
 * CU14/CU15/CU16. El botón "Reservar" nunca se oculta de forma permanente:
 * tras reservar (o agregar) se cierra el modal correspondiente, se emite
 * `reservado` para que producto-detalle limpie la sucursal elegida (ver
 * onReservaCreada), y este componente limpia su propio estado -- listo para
 * una reserva nueva.
 *
 * La validación real de fecha/horario/disponibilidad/compatibilidad ocurre
 * SIEMPRE en el backend (ver CU17 service.py); este componente solo arma la
 * interfaz con las mismas reglas (ver horario-reserva.ts) y envía la
 * intención.
 */
@Component({
  selector: 'app-crear-reserva',
  imports: [Icon],
  templateUrl: './crear-reserva.html',
  styleUrl: './crear-reserva.scss',
})
export class CrearReserva {
  private readonly auth = inject(AuthService);
  private readonly service = inject(CrearReservaService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);
  protected readonly connectivity = inject(ConnectivityService);
  private readonly offlineStorage = inject(OfflineStorageService);

  readonly productoVarianteId = input<number | null>(null);
  readonly sucursalId = input<number | null>(null);
  readonly sucursalNombre = input<string | null>(null);
  readonly returnUrl = input<string>('/');
  // Vienen del returnUrl al volver del login (ver producto-detalle.ts) --
  // strings crudos sin validar todavía; este componente decide si siguen
  // siendo válidos antes de confiar en ellos (ver efecto en el constructor).
  readonly fechaRestaurada = input<string | null>(null);
  readonly horaRestaurada = input<string | null>(null);
  readonly reservado = output<void>();

  protected readonly isAuthenticated = this.auth.isAuthenticated;
  protected readonly submitting = signal(false);
  protected readonly modalAbierto = signal(false);
  protected readonly fechaSeleccionada = signal<string | null>(null);
  protected readonly horaSeleccionada = signal<string | null>(null);

  protected readonly dias = proximosDias();

  protected readonly bloquesDisponibles = computed<string[]>(() => {
    const fecha = this.fechaSeleccionada();
    return fecha ? bloquesHorarioDisponibles(fecha) : [];
  });

  // Modal "Tienes una reserva pendiente en esta sucursal" -- se abre EN VEZ
  // del modal de fecha/hora cuando existen reservas compatibles.
  protected readonly modalCompatiblesAbierto = signal(false);
  protected readonly verificandoCompatibles = signal(false);
  protected readonly reservasCompatibles = signal<ReservaOut[]>([]);
  protected readonly agregando = signal(false);
  protected readonly formatearFecha = formatearFechaReserva;
  protected readonly formatearHorario = formatearHorarioReserva;

  private restauracionAplicada = false;

  constructor() {
    // Se ejecuta en cada cambio de inputs, pero solo actúa una vez que hay
    // sucursal (ya restaurada por el padre) y fecha/hora del returnUrl --
    // restauracionAplicada evita repetirlo si el Cliente reabre/cierra el
    // modal manualmente después.
    effect(() => {
      const sucursalId = this.sucursalId();
      const fecha = this.fechaRestaurada();
      const hora = this.horaRestaurada();
      if (this.restauracionAplicada || sucursalId === null || !fecha || !hora) {
        return;
      }
      const fechaValida = fecha >= hoyIso() && fecha <= fechaMaximaIso();
      const horaValida = fechaValida && bloquesHorarioDisponibles(fecha).includes(hora);
      if (!(fechaValida && horaValida)) {
        return;
      }
      this.restauracionAplicada = true;
      this.fechaSeleccionada.set(fecha);
      this.horaSeleccionada.set(hora);
      // Recién volviendo del login ya hay sesión -- antes de reabrir
      // directo el modal de fecha/hora restaurado, se revisa si ahora
      // conviene ofrecer "agregar a una reserva existente" en su lugar. La
      // fecha/hora restaurada queda igual disponible para "Programar otra
      // visita" o para el caso sin compatibles.
      this._verificarCompatiblesOAbrirModalFecha(sucursalId);
    });
  }

  protected get esCliente(): boolean {
    return this.auth.hasRole('CLIENTE');
  }

  protected get haySeleccionBase(): boolean {
    return this.productoVarianteId() !== null && this.sucursalId() !== null;
  }

  protected get puedeConfirmar(): boolean {
    return (
      this.haySeleccionBase &&
      this.fechaSeleccionada() !== null &&
      this.horaSeleccionada() !== null &&
      !this.submitting()
    );
  }

  abrir(): void {
    if (!this.haySeleccionBase) {
      return;
    }
    if (!this.isAuthenticated()) {
      // Sin sesión no hay cliente_id con el que consultar compatibles --
      // mismo flujo de siempre, la sesión se verifica recién al confirmar.
      this.modalAbierto.set(true);
      return;
    }
    this._verificarCompatiblesOAbrirModalFecha(this.sucursalId()!);
  }

  private _verificarCompatiblesOAbrirModalFecha(sucursalId: number): void {
    this.verificandoCompatibles.set(true);
    this.service.listarCompatibles(sucursalId).subscribe({
      next: (reservas) => {
        this.verificandoCompatibles.set(false);
        if (reservas.length > 0) {
          this.reservasCompatibles.set(reservas);
          this.modalCompatiblesAbierto.set(true);
        } else {
          this.modalAbierto.set(true);
        }
      },
      error: () => {
        // Una consulta fallida no debe bloquear el flujo -- sigue como si
        // no hubiera reservas compatibles.
        this.verificandoCompatibles.set(false);
        this.modalAbierto.set(true);
      },
    });
  }

  cerrar(): void {
    this.modalAbierto.set(false);
  }

  cerrarModalCompatibles(): void {
    if (this.agregando()) {
      return;
    }
    this.modalCompatiblesAbierto.set(false);
  }

  elegirAgregarAReserva(reserva: ReservaOut): void {
    if (this.agregando() || !this.haySeleccionBase) {
      return;
    }
    this.agregando.set(true);
    this.service
      .agregarDetalle(reserva.id, { producto_variante_id: this.productoVarianteId()!, cantidad: 1 })
      .subscribe({
        next: (actualizada) => {
          this.agregando.set(false);
          this.modalCompatiblesAbierto.set(false);
          this.toast.brand(`Prenda agregada a la reserva ${actualizada.codigo_reserva}.`);
          this.reservado.emit();
        },
        error: (err) => {
          this.agregando.set(false);
          const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
          this.toast.error(detalle ?? 'No se pudo agregar la prenda a la reserva. Inténtalo nuevamente.');
        },
      });
  }

  elegirProgramarOtraVisita(): void {
    if (this.agregando()) {
      return;
    }
    this.modalCompatiblesAbierto.set(false);
    this.modalAbierto.set(true);
  }

  seleccionarFecha(iso: string, esDomingo: boolean): void {
    if (esDomingo) {
      return;
    }
    this.fechaSeleccionada.set(iso);
    this.horaSeleccionada.set(null);
  }

  seleccionarHora(hora: string): void {
    this.horaSeleccionada.set(hora);
  }

  confirmar(): void {
    console.log('[CU8 CONFIRM] Iniciando flujo de confirmación');
    if (!this.puedeConfirmar) {
      console.log('[CU8 CONFIRM] Validación de entrada fallida');
      return;
    }

    if (!this.isAuthenticated()) {
      console.log('[CU8 CONFIRM] No autenticado, redirigiendo a login');
      const url = `${this.returnUrl()}&fecha=${this.fechaSeleccionada()}&hora=${this.horaSeleccionada()}`;
      this.router.navigate(['/login'], { queryParams: { returnUrl: url } });
      return;
    }

    // CU8 -- Bifurcación online/offline
    const isOnline = this.connectivity.isOnline();
    console.log(`[CU8 BIFURCACION] isOnline()=${isOnline}`);

    if (!isOnline) {
      console.log('[CU8 BIFURCACION] ✅ Entra a OFFLINE — usando IndexedDB');
      this._crearReservaOffline();
      return;
    }

    console.log('[CU8 BIFURCACION] ❌ Entra a ONLINE — usando HTTP');
    this._crearReservaOnline();
  }

  private async _crearReservaOffline(): Promise<void> {
    console.log('[CU8 OFFLINE] Iniciando guardado en IndexedDB — NO se harán peticiones HTTP');
    const usuario = this.auth.usuario();
    if (!usuario) {
      this.toast.error('No hay sesión activa. Inténtalo nuevamente.');
      return;
    }

    this.submitting.set(true);

    try {
      const empresaId = usuario.empresa_id || 0;
      const sucursalId = this.sucursalId()!;
      const productoVarianteId = this.productoVarianteId()!;
      const cantidad = 1;
      const fecha = this.fechaSeleccionada()!;
      const hora = this.horaSeleccionada()!;

      // Validación 1: Verificar que existe preparación local (CU6)
      console.log(`[CU8] Validación 1: Buscando preparación para empresa=${empresaId}, sucursal=${sucursalId}`);
      const preparacion = await this.offlineStorage.getPreparacionActual(empresaId, sucursalId);
      console.log(`[CU8] Validación 1 resultado:`, preparacion);
      if (!preparacion) {
        this.submitting.set(false);
        this.toast.error('No hay datos locales disponibles. Descarga la información nuevamente.');
        return;
      }
      console.log(`[CU8] Validación 1: ✅ PASADA`);

      // Validación 2: Verificar sucursal pertenece a empresa
      if (!this.offlineStorage.validarSucursalPertenece(preparacion, sucursalId, empresaId)) {
        this.submitting.set(false);
        this.toast.error('La sucursal seleccionada no pertenece a tu empresa.');
        return;
      }

      // Validación 3: Verificar variante existe en datos locales
      const variante = this.offlineStorage.getVariantePorId(preparacion, productoVarianteId);
      if (!variante) {
        this.submitting.set(false);
        this.toast.error('La variante seleccionada no existe o no está disponible.');
        return;
      }

      // Validación 4: Verificar cantidad es número entero positivo
      if (!Number.isInteger(cantidad) || cantidad <= 0) {
        this.submitting.set(false);
        this.toast.error('La cantidad debe ser un número entero positivo.');
        return;
      }

      // Validación 5: Verificar stock local suficiente
      if (variante.stock_disponible < cantidad) {
        this.submitting.set(false);
        this.toast.error(
          `Stock insuficiente. Disponible: ${variante.stock_disponible}, solicitado: ${cantidad}`
        );
        return;
      }

      // Validación 6: Verificar fecha y hora son válidas (usando reglas de CU7)
      const hoy = hoyIso();
      const fechaMaxima = fechaMaximaIso();
      if (fecha < hoy || fecha > fechaMaxima) {
        this.submitting.set(false);
        this.toast.error('La fecha seleccionada está fuera del rango permitido (próximos 7 días).');
        return;
      }

      const bloqueValido = bloquesHorarioDisponibles(fecha).includes(hora);
      if (!bloqueValido) {
        this.submitting.set(false);
        this.toast.error('La hora seleccionada no es válida para esta fecha.');
        return;
      }

      // Todas las validaciones pasaron — guardar reserva offline
      const uuid = generarUUID();
      const ahora = new Date().toISOString();

      const reservaOffline = {
        uuid,
        empresa_id: empresaId,
        cliente_id: usuario.id,
        sucursal_id: sucursalId,
        fecha_reserva: fecha,
        hora_inicio: hora,
        estado_general: 'PENDIENTE',
        estado_sync: 'PENDIENTE_SYNC',
        fecha_creacion_local: ahora,
        detalles: [
          {
            uuid: generarUUID(),
            producto_variante_id: productoVarianteId,
            cantidad,
            estado: 'PENDIENTE',
            estado_sync: 'PENDIENTE_SYNC',
          },
        ],
      };

      await this.offlineStorage.saveReservaOffline(reservaOffline, empresaId);

      this.submitting.set(false);
      this.modalAbierto.set(false);
      this.fechaSeleccionada.set(null);
      this.horaSeleccionada.set(null);
      this.toast.brand(`Reserva guardada localmente (offline). UUID: ${uuid}`);
      this.reservado.emit();
    } catch (error) {
      this.submitting.set(false);
      console.error('[CU08 ERROR]', error);
      this.toast.error('No se pudo guardar la reserva offline. Inténtalo nuevamente.');
    }
  }

  private _crearReservaOnline(): void {
    this.submitting.set(true);
    const reservaUuid = generarUUID();  // Generar UUID UNA SOLA VEZ
    this.service
      .crear({
        producto_variante_id: this.productoVarianteId()!,
        sucursal_id: this.sucursalId()!,
        cantidad: 1,
        fecha_reserva: this.fechaSeleccionada()!,
        hora_inicio: this.horaSeleccionada()!,
      })
      .subscribe({
        next: (reserva) => {
          this.submitting.set(false);
          this.modalAbierto.set(false);
          this.fechaSeleccionada.set(null);
          this.horaSeleccionada.set(null);
          this.toast.brand(`Reserva creada correctamente. Código: ${reserva.codigo_reserva}`);
          this.reservado.emit();
        },
        error: (err) => {
          this.submitting.set(false);
          console.log('[CU8 ERROR]', { status: err?.status, error: err?.error, message: err?.message });
          // Si falla por error de transporte (status 0/null o sin respuesta del servidor), guardar offline
          const esErrorTransporte = err?.status === 0 || err?.status === null || !err?.status;
          if (esErrorTransporte) {
            console.log('[CU8] Detectado error de transporte, activando fallback offline');
            void this._guardarReservaComFallback(reservaUuid);
            return;
          }
          const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
          this.toast.error(detalle ?? 'No se pudo crear la reserva. Inténtalo nuevamente.');
        },
      });
  }

  private async _guardarReservaComFallback(reservaUuid: string): Promise<void> {
    try {
      const usuario = this.auth.usuario();
      if (!usuario) {
        this.toast.error('No hay sesión activa.');
        return;
      }

      const empresaId = usuario.empresa_id || 0;
      const sucursalId = this.sucursalId()!;
      const productoVarianteId = this.productoVarianteId()!;
      const fecha = this.fechaSeleccionada()!;
      const hora = this.horaSeleccionada()!;

      // Reutilizar validaciones del flujo offline
      const preparacion = await this.offlineStorage.getPreparacionActual(empresaId, sucursalId);
      if (!preparacion) {
        this.toast.error('No hay datos locales disponibles. Descarga la información nuevamente.');
        return;
      }

      const variante = this.offlineStorage.getVariantePorId(preparacion, productoVarianteId);
      if (!variante || variante.stock_disponible < 1) {
        this.toast.error(
          `Stock insuficiente. Disponible: ${variante?.stock_disponible || 0}`
        );
        return;
      }

      const ahora = new Date().toISOString();

      // Construir reserva offline con UUID reutilizado del intento online
      const reservaOffline = {
        uuid: reservaUuid,
        empresa_id: empresaId,
        cliente_id: usuario.id,
        sucursal_id: sucursalId,
        fecha_reserva: fecha,
        hora_inicio: hora,
        estado_general: 'PENDIENTE',
        estado_sync: 'PENDIENTE_SYNC',
        fecha_creacion_local: ahora,
        detalles: [
          {
            uuid: generarUUID(),
            producto_variante_id: productoVarianteId,
            cantidad: 1,
            estado: 'PENDIENTE',
            estado_sync: 'PENDIENTE_SYNC',
          },
        ],
      };

      // Guardar en IndexedDB
      await this.offlineStorage.saveReservaOffline(reservaOffline, empresaId);

      // Éxito: cerrar modal y mostrar feedback
      this.modalAbierto.set(false);
      this.fechaSeleccionada.set(null);
      this.horaSeleccionada.set(null);
      this.toast.brand(`Reserva guardada offline. Se sincronizará cuando recuperes conexión.`);
      this.reservado.emit();
    } catch (error) {
      console.error('[CU8 FALLBACK]', error);
      this.toast.error('No se pudo guardar la reserva localmente. Inténtalo nuevamente.');
    }
  }
}
