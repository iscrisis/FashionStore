import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { ComprobanteDetalle } from '../../comprobantes/comprobante-detalle/comprobante-detalle';
import { ComprobanteVentaOut } from '../../comprobantes/comprobante.model';
import { ComprobanteService, descargarBlob } from '../../comprobantes/comprobante.service';

/**
 * CU31 -- Emitir comprobante de venta (Cliente). Vive dentro del layout
 * público ('/comprobante/:ventaId', mismo navbar de FashionStore que
 * '/mi-perfil' y '/mis-reservas' -- ver app.routes.ts), no es un dashboard
 * nuevo. A la que navega el botón "Ver comprobante" de resultado-pago.ts
 * (CU23) apenas se confirma el pago.
 *
 * El backend ya resuelve la autorización SIEMPRE del token (`venta.cliente_id
 * == actor.id`, ver CU31_EmitirComprobanteVenta/service.py) -- este
 * componente nunca decide ni envía de quién es la venta, solo el `venta_id`
 * de la URL. Reutiliza <app-comprobante-detalle> (mismo componente que usa
 * el Cajero) para el detalle, nunca duplicado.
 */
@Component({
  selector: 'app-comprobante-cliente',
  imports: [RouterLink, ComprobanteDetalle],
  templateUrl: './comprobante-cliente.html',
  styleUrl: './comprobante-cliente.scss',
})
export class ComprobanteCliente implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(ComprobanteService);
  private readonly toast = inject(ToastService);

  protected readonly cargando = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly comprobante = signal<ComprobanteVentaOut | null>(null);
  protected readonly descargando = signal(false);

  ngOnInit(): void {
    const ventaId = Number(this.route.snapshot.paramMap.get('ventaId'));
    if (!ventaId) {
      this.cargando.set(false);
      this.errorMessage.set('Comprobante no encontrado.');
      return;
    }

    this.service.obtener(ventaId).subscribe({
      next: (comprobante) => {
        this.cargando.set(false);
        this.comprobante.set(comprobante);
      },
      error: (err) => {
        this.cargando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.errorMessage.set(detalle ?? 'No se pudo cargar el comprobante. Inténtalo nuevamente.');
      },
    });
  }

  descargar(): void {
    const comprobante = this.comprobante();
    if (!comprobante || this.descargando()) {
      return;
    }
    this.descargando.set(true);
    this.service.descargarPdf(comprobante.venta_id).subscribe({
      next: (blob) => {
        this.descargando.set(false);
        descargarBlob(blob, `${comprobante.codigo_venta}.pdf`);
      },
      error: () => {
        this.descargando.set(false);
        this.toast.error('No se pudo descargar el comprobante. Inténtalo nuevamente.');
      },
    });
  }
}
