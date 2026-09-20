import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { formatearFechaReserva, formatearHorarioReserva } from '../reserva-formato';
import { ReservaOut } from './crear-reserva.model';
import { CrearReservaService } from './crear-reserva.service';
import { bloquesHorarioDisponibles, fechaMaximaIso, hoyIso, proximosDias } from './horario-reserva';

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
    if (!this.puedeConfirmar) {
      return;
    }

    if (!this.isAuthenticated()) {
      const url = `${this.returnUrl()}&fecha=${this.fechaSeleccionada()}&hora=${this.horaSeleccionada()}`;
      this.router.navigate(['/login'], { queryParams: { returnUrl: url } });
      return;
    }

    this.submitting.set(true);
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
          const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
          this.toast.error(detalle ?? 'No se pudo crear la reserva. Inténtalo nuevamente.');
        },
      });
  }
}
