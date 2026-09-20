import { Component, input, output } from '@angular/core';
import { Icon } from '../../../../core/ui/icon/icon';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { VentaPresencialOut } from '../venta-presencial.model';

/**
 * CU24 -- Registrar venta presencial (Cajero). Resumen final, único
 * consumidor: `venta-directa.ts` (venta DIRECTA) -- "VENTA PRESENCIAL",
 * código VT-XXXXX, las prendas y el total.
 *
 * CONTINUAR AL PAGO emite `continuarPago`: el padre (venta-directa.ts)
 * decide qué hacer con eso -- abrir el modal de CU25
 * (features/cajero/ventas/procesar-pago), el ÚNICO componente de pago,
 * reutilizado también desde reservas-pendientes.html ("Cargar venta"). Este
 * componente nunca conoce el modal ni el pago en sí, solo emite la
 * intención.
 */
@Component({
  selector: 'app-venta-resumen',
  imports: [Icon],
  templateUrl: './venta-resumen.html',
  styleUrl: './venta-resumen.scss',
})
export class VentaResumen {
  readonly venta = input.required<VentaPresencialOut>();
  readonly volver = output<void>();
  readonly continuarPago = output<void>();

  protected readonly resolveMediaUrl = resolveMediaUrl;

  onVolver(): void {
    this.volver.emit();
  }

  onContinuarPago(): void {
    this.continuarPago.emit();
  }
}
