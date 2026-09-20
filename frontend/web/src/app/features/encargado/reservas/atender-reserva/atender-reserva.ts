import { Component, inject, input, output, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { ToastService } from '../../../../core/ui/toast/toast.service';
import { EstadoReservaPanel, ReservaDetallePanel } from '../reservas.model';
import { PanelReservasService } from '../reservas.service';

/**
 * CU20 -- Atender reserva de prendas (Encargado de Sucursal), acciones a
 * nivel DETALLE (una prenda dentro de una reserva).
 *
 * Se embebe una vez por PRENDA dentro del panel "Reservas" (ver
 * reservas.html) -- estas acciones afectan SOLO esa prenda, nunca al resto
 * de la misma reserva ni a su cabecera. "Confirmar llegada" y "Finalizar
 * atención" NO viven aquí -- son acciones de la RESERVA completa (un solo
 * botón por reserva, ver reservas.ts) -- por eso este componente necesita
 * `estadoGeneralReserva` además de `detalle()`: sin saber si la reserva ya
 * está EN_ATENCION, no puede decidir si corresponde ofrecer "No la compra"/
 * "Enviar a caja".
 *
 * Botones según `detalle().estado` y `estadoGeneralReserva()`:
 *   - PENDIENTE: "Preparar prenda" (acción directa, sin modal -- paso de
 *     bajo riesgo, reversible en la práctica. No modifica stock).
 *   - PREPARADA, con la reserva YA en_atención: "No la compra" y "Enviar a
 *     caja" -- la decisión del Encargado tras probarse la prenda. Ninguna
 *     de las dos libera/toca stock de inmediato: eso ocurre recién cuando
 *     el Encargado presiona "Finalizar atención" de TODA la reserva (ver
 *     reservas.ts) -- por eso ninguna de las dos pide confirmación aparte,
 *     la decisión sigue siendo reversible (puede cambiarla presionando la
 *     otra opción) hasta ese cierre final.
 *   - PREPARADA, pero la reserva TODAVÍA no está en_atención: sin acciones
 *     -- hay que confirmar la llegada del Cliente primero (a nivel reserva).
 *   - Cualquier otro estado (LISTA_PARA_CAJA, ATENDIDA, CANCELADA, VENCIDA):
 *     ya tiene una decisión tomada, solo lectura.
 *
 * Todas las transiciones las valida SIEMPRE el backend (PATCH
 * /reservas/detalles/{id}/...) -- este componente nunca decide si una acción
 * es válida más allá de qué botones ofrecer.
 */
@Component({
  selector: 'app-atender-reserva',
  templateUrl: './atender-reserva.html',
  styleUrl: './atender-reserva.scss',
})
export class AtenderReserva {
  private readonly service = inject(PanelReservasService);
  private readonly toast = inject(ToastService);

  readonly detalle = input.required<ReservaDetallePanel>();
  readonly estadoGeneralReserva = input.required<EstadoReservaPanel>();
  readonly actualizada = output<ReservaDetallePanel>();

  protected readonly procesando = signal(false);

  protected get puedeDecidir(): boolean {
    return this.estadoGeneralReserva() === 'EN_ATENCION' && this.detalle().estado === 'PREPARADA';
  }

  preparar(): void {
    this._ejecutar(this.service.preparar(this.detalle().id), 'Prenda marcada como preparada.');
  }

  noLaCompra(): void {
    this._ejecutar(this.service.noLaCompra(this.detalle().id), 'Decisión guardada: no la compra.');
  }

  enviarACaja(): void {
    this._ejecutar(this.service.enviarACaja(this.detalle().id), 'Decisión guardada: va a caja.');
  }

  private _ejecutar(accion: Observable<ReservaDetallePanel>, mensajeExito: string): void {
    if (this.procesando()) {
      return;
    }
    this.procesando.set(true);
    accion.subscribe({
      next: (actualizada) => {
        this.procesando.set(false);
        this.toast.brand(mensajeExito);
        this.actualizada.emit(actualizada);
      },
      error: (err) => {
        this.procesando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo completar la acción. Inténtalo nuevamente.');
      },
    });
  }
}
