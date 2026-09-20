import { Component, OnInit, computed, inject, input, output, signal } from '@angular/core';
import { Icon } from '../../../../core/ui/icon/icon';
import { ToastService } from '../../../../core/ui/toast/toast.service';
import {
  DetalleDevolucionOut,
  RegistrarCambioPayload,
  VarianteCambioOut,
} from '../devolucion-cambio.model';
import { DevolucionCambioService } from '../devolucion-cambio.service';

/**
 * CU26 -- Cambiar prenda. Ficha modal centrada, mismo patrón que
 * devolver-modal.ts. MVP: solo permite cambiar por otra variante del MISMO
 * producto -- las opciones que ofrece este modal ya vienen filtradas así
 * por el backend (ver CU26_RegistrarDevolucionCambio/service.py,
 * opciones_cambio), nunca se arma la lista con productos distintos.
 *
 * El disponible de cada opción es SIEMPRE `stock_actual - stock_reservado`
 * de la sucursal de la Venta -- la cantidad máxima a cambiar queda acotada
 * por el menor entre eso y lo que todavía puede cambiarse de la línea
 * original (`detalle().cantidad_disponible`), pero es solo un límite de UI:
 * FastAPI vuelve a validar todo al confirmar.
 */
@Component({
  selector: 'app-cambiar-modal',
  imports: [Icon],
  templateUrl: './cambiar-modal.html',
  styleUrl: './cambiar-modal.scss',
})
export class CambiarModal implements OnInit {
  private readonly service = inject(DevolucionCambioService);
  private readonly toast = inject(ToastService);

  readonly ventaId = input.required<number>();
  readonly detalle = input.required<DetalleDevolucionOut>();
  readonly cerrar = output<void>();
  readonly registrada = output<void>();

  protected readonly cargando = signal(true);
  protected readonly opciones = signal<VarianteCambioOut[]>([]);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly varianteSeleccionada = signal<VarianteCambioOut | null>(null);
  protected readonly cantidad = signal(1);
  protected readonly enviando = signal(false);

  protected readonly maxCantidad = computed(() => {
    const variante = this.varianteSeleccionada();
    const disponibleOriginal = this.detalle().cantidad_disponible;
    return variante ? Math.min(disponibleOriginal, variante.disponible) : disponibleOriginal;
  });

  protected readonly puedeConfirmar = computed(() => {
    if (this.enviando()) {
      return false;
    }
    const variante = this.varianteSeleccionada();
    if (!variante || variante.disponible <= 0) {
      return false;
    }
    const cantidad = this.cantidad();
    return cantidad >= 1 && cantidad <= this.maxCantidad();
  });

  ngOnInit(): void {
    this.service.opcionesCambio(this.ventaId(), this.detalle().venta_detalle_id).subscribe({
      next: (opciones) => {
        this.opciones.set(opciones);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.errorMessage.set('No se pudieron cargar las variantes disponibles.');
      },
    });
  }

  seleccionarVariante(variante: VarianteCambioOut): void {
    if (variante.disponible <= 0) {
      return;
    }
    this.varianteSeleccionada.set(variante);
    this.cantidad.set(1);
  }

  incrementar(): void {
    if (this.cantidad() < this.maxCantidad()) {
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
    this.cantidad.set(Math.min(Math.max(Math.round(numero), 1), this.maxCantidad()));
  }

  confirmar(): void {
    const variante = this.varianteSeleccionada();
    if (!variante || !this.puedeConfirmar()) {
      return;
    }
    this.enviando.set(true);
    const payload: RegistrarCambioPayload = {
      venta_id: this.ventaId(),
      venta_detalle_id: this.detalle().venta_detalle_id,
      cantidad: this.cantidad(),
      variante_nueva_id: variante.producto_variante_id,
    };
    this.service.registrarCambio(payload).subscribe({
      next: () => {
        this.enviando.set(false);
        this.toast.success('Cambio registrado.');
        this.registrada.emit();
      },
      error: (err) => {
        this.enviando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo registrar el cambio. Inténtalo nuevamente.');
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
