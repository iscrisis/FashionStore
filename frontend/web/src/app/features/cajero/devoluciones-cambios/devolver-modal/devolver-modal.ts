import { Component, computed, inject, input, output, signal } from '@angular/core';
import { Icon } from '../../../../core/ui/icon/icon';
import { ToastService } from '../../../../core/ui/toast/toast.service';
import { DetalleDevolucionOut, MotivoDevolucion, RegistrarDevolucionPayload } from '../devolucion-cambio.model';
import { DevolucionCambioService } from '../devolucion-cambio.service';

/**
 * CU26 -- Devolver prenda. Ficha modal centrada sobre la pantalla de
 * devoluciones-cambios.ts (mismo patrón que procesar-pago.ts, CU25): fondo
 * oscurecido, nunca navega a otra página. Recibe la línea (`detalle`) YA
 * calculada por el backend (`cantidad_disponible`) -- este modal nunca
 * decide cuánto puede devolverse, solo limita la UI a ese tope; FastAPI
 * vuelve a validarlo todo al confirmar (ver CU26_RegistrarDevolucionCambio/
 * service.py).
 */
@Component({
  selector: 'app-devolver-modal',
  imports: [Icon],
  templateUrl: './devolver-modal.html',
  styleUrl: './devolver-modal.scss',
})
export class DevolverModal {
  private readonly service = inject(DevolucionCambioService);
  private readonly toast = inject(ToastService);

  readonly ventaId = input.required<number>();
  readonly detalle = input.required<DetalleDevolucionOut>();
  readonly cerrar = output<void>();
  readonly registrada = output<void>();

  protected readonly cantidad = signal(1);
  protected readonly motivo = signal<MotivoDevolucion | null>(null);
  protected readonly observacion = signal('');
  protected readonly enviando = signal(false);

  protected readonly puedeConfirmar = computed(() => {
    if (this.enviando()) {
      return false;
    }
    const cantidad = this.cantidad();
    if (cantidad < 1 || cantidad > this.detalle().cantidad_disponible) {
      return false;
    }
    const motivo = this.motivo();
    if (!motivo) {
      return false;
    }
    return motivo !== 'OTRO' || this.observacion().trim().length > 0;
  });

  incrementar(): void {
    if (this.cantidad() < this.detalle().cantidad_disponible) {
      this.cantidad.update((c) => c + 1);
    }
  }

  decrementar(): void {
    if (this.cantidad() > 1) {
      this.cantidad.update((c) => c - 1);
    }
  }

  actualizarCantidad(valor: string): void {
    const numero = Number(valor);
    if (!Number.isFinite(numero)) {
      return;
    }
    const max = this.detalle().cantidad_disponible;
    this.cantidad.set(Math.min(Math.max(Math.round(numero), 1), max));
  }

  seleccionarMotivo(motivo: MotivoDevolucion): void {
    this.motivo.set(motivo);
  }

  actualizarObservacion(valor: string): void {
    this.observacion.set(valor);
  }

  confirmar(): void {
    const motivo = this.motivo();
    if (!motivo || !this.puedeConfirmar()) {
      return;
    }
    this.enviando.set(true);
    const observacion = this.observacion().trim();
    const payload: RegistrarDevolucionPayload = {
      venta_id: this.ventaId(),
      venta_detalle_id: this.detalle().venta_detalle_id,
      cantidad: this.cantidad(),
      motivo,
      ...(motivo === 'OTRO' && observacion ? { observacion } : {}),
    };
    this.service.registrarDevolucion(payload).subscribe({
      next: () => {
        this.enviando.set(false);
        this.toast.success('Devolución registrada.');
        this.registrada.emit();
      },
      error: (err) => {
        this.enviando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo registrar la devolución. Inténtalo nuevamente.');
      },
    });
  }

  onCerrar(): void {
    if (this.enviando()) {
      return;
    }
    this.cerrar.emit();
  }
}
