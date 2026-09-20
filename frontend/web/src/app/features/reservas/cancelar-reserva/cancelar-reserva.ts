import { Component, inject, input, output, signal } from '@angular/core';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { Icon } from '../../../core/ui/icon/icon';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { ReservaDetalleOut, ReservaOut } from '../crear-reserva/crear-reserva.model';
import { formatearFechaReserva, formatearHorarioReserva } from '../reserva-formato';
import { CancelarReservaService } from './cancelar-reserva.service';

/**
 * CU19 -- Cancelar reserva (Cliente).
 *
 * Se embebe una vez por PRENDA (detalle) dentro de "Mis reservas" (CU18, ver
 * mis-reservas.html) -- cancela esa prenda sin afectar al resto de la misma
 * reserva (`reserva` solo se usa para el resumen del modal: sucursal, fecha,
 * horario). Decide sola si mostrar el botón "Cancelar" (solo si esa prenda
 * todavía no llegó a la sucursal: PENDIENTE o PREPARADA, ver puedeCancelar)
 * -- desde EN_ATENCION en adelante (CU20 -- Atender reserva) no muestra
 * nada, igual que pide CU19.
 *
 * Al presionarlo NO cancela directamente: abre un modal de confirmación con
 * el mismo lenguaje visual que el modal de CU17 (Programar reserva, ver
 * crear-reserva.ts/scss) -- overlay + tarjeta centrada en desktop/tablet,
 * hoja inferior en móvil. Recién al presionar "Cancelar" dentro del modal
 * llama al backend (PATCH /reservas/detalles/{id}/cancelar, que YA resuelve
 * el dueño desde el token -- este componente nunca decide ni envía de quién
 * es la reserva).
 *
 * Al confirmar: cierra el modal, emite el DETALLE ya actualizado (estado
 * CANCELADA) para que MisReservas reemplace esa única prenda sin recargar
 * toda la lista (ver onDetalleCancelado en mis-reservas.ts), y muestra un
 * toast "brand" (rojo FashionStore, no verde -- mismo tipo que ya usa CU17
 * para su confirmación, ver ToastService).
 */
@Component({
  selector: 'app-cancelar-reserva',
  imports: [Icon],
  templateUrl: './cancelar-reserva.html',
  styleUrl: './cancelar-reserva.scss',
})
export class CancelarReserva {
  private readonly service = inject(CancelarReservaService);
  private readonly toast = inject(ToastService);

  readonly reserva = input.required<ReservaOut>();
  readonly detalle = input.required<ReservaDetalleOut>();
  readonly cancelada = output<ReservaDetalleOut>();

  protected readonly resolveMediaUrl = resolveMediaUrl;
  protected readonly modalAbierto = signal(false);
  protected readonly cancelando = signal(false);

  // CU20 (Atender reserva de prendas) amplió los estados: cancelar sigue
  // permitido mientras esa prenda todavía no haya llegado a la sucursal
  // (PENDIENTE o PREPARADA) -- desde EN_ATENCION en adelante el Encargado ya
  // empezó a atenderla (ver backend CU19_CancelarReserva/service.py).
  protected get puedeCancelar(): boolean {
    return this.detalle().estado === 'PENDIENTE' || this.detalle().estado === 'PREPARADA';
  }

  protected get fecha(): string {
    return formatearFechaReserva(this.reserva().fecha_reserva);
  }

  protected get horario(): string {
    return formatearHorarioReserva(this.reserva().hora_inicio, this.reserva().hora_fin);
  }

  abrir(): void {
    this.modalAbierto.set(true);
  }

  cerrar(): void {
    if (this.cancelando()) {
      return;
    }
    this.modalAbierto.set(false);
  }

  confirmar(): void {
    if (this.cancelando()) {
      return;
    }
    this.cancelando.set(true);
    this.service.cancelarDetalle(this.detalle().id).subscribe({
      next: (actualizado) => {
        this.cancelando.set(false);
        this.modalAbierto.set(false);
        this.toast.brand('Prenda cancelada correctamente.');
        this.cancelada.emit(actualizado);
      },
      error: (err) => {
        this.cancelando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo cancelar la reserva. Inténtalo nuevamente.');
      },
    });
  }
}
