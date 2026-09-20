import { Component, input } from '@angular/core';
import { Icon } from '../../../core/ui/icon/icon';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { ComprobanteVentaOut, MetodoPagoComprobante } from '../comprobante.model';

/**
 * CU31 -- Emitir comprobante de venta. Presentación PURA del comprobante ya
 * cargado (`comprobante`, input required) -- nunca hace fetch ni conoce
 * rutas: features/cliente/comprobantes y features/cajero/comprobantes lo
 * envuelven cada uno con su propio layout (navbar público vs sidebar de
 * Cajero) y sus propias acciones (Descargar / Enviar), sin duplicar este
 * marcado ni sus estilos -- "si existe un componente reutilizable de
 * detalle de venta: reutilizarlo" (requerimiento de CU31).
 */
@Component({
  selector: 'app-comprobante-detalle',
  imports: [Icon],
  templateUrl: './comprobante-detalle.html',
  styleUrl: './comprobante-detalle.scss',
})
export class ComprobanteDetalle {
  readonly comprobante = input.required<ComprobanteVentaOut>();

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected etiquetaMetodo(metodo: MetodoPagoComprobante): string {
    const etiquetas: Record<MetodoPagoComprobante, string> = {
      STRIPE: 'Stripe',
      EFECTIVO: 'Efectivo',
      TARJETA: 'Tarjeta',
      QR: 'QR',
    };
    return etiquetas[metodo] ?? metodo;
  }

  protected fecha(iso: string): string {
    const fecha = new Date(iso);
    const dd = String(fecha.getDate()).padStart(2, '0');
    const mm = String(fecha.getMonth() + 1).padStart(2, '0');
    const hh = String(fecha.getHours()).padStart(2, '0');
    const min = String(fecha.getMinutes()).padStart(2, '0');
    return `${dd}/${mm}/${fecha.getFullYear()} ${hh}:${min}`;
  }
}
