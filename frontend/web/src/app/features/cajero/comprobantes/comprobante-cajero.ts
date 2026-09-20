import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { ComprobanteDetalle } from '../../comprobantes/comprobante-detalle/comprobante-detalle';
import { ComprobanteVentaOut } from '../../comprobantes/comprobante.model';
import { ComprobanteService, descargarBlob } from '../../comprobantes/comprobante.service';

/**
 * CU31 -- Emitir comprobante de venta (Cajero). Vive bajo CajeroLayout
 * ('/cajero/comprobante/:ventaId') -- a la que navega el botón "Ver" del
 * paso "PAGO REGISTRADO" de procesar-pago.ts (CU25), apenas se confirma un
 * pago presencial.
 *
 * El backend ya resuelve la autorización SIEMPRE del token
 * (`venta.sucursal_id == actor.sucursal_id`, ver
 * CU31_EmitirComprobanteVenta/service.py) -- este componente nunca decide ni
 * envía de qué sucursal es la venta, solo el `venta_id` de la URL. Reutiliza
 * <app-comprobante-detalle> (mismo componente que usa el Cliente), nunca
 * duplicado.
 *
 * "Enviar" SOLO se muestra si la venta tiene un Cliente registrado
 * (`comprobante.cliente !== null`) -- una venta directa de mostrador
 * (CU24, sin Cliente) nunca lo obliga a registrar un correo, mismo
 * requerimiento de CU31.
 */
@Component({
  selector: 'app-comprobante-cajero',
  imports: [ComprobanteDetalle],
  templateUrl: './comprobante-cajero.html',
  styleUrl: './comprobante-cajero.scss',
})
export class ComprobanteCajero implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(ComprobanteService);
  private readonly toast = inject(ToastService);

  protected readonly cargando = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly comprobante = signal<ComprobanteVentaOut | null>(null);
  protected readonly descargando = signal(false);
  protected readonly enviando = signal(false);

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

  enviar(): void {
    const comprobante = this.comprobante();
    if (!comprobante || this.enviando()) {
      return;
    }
    this.enviando.set(true);
    this.service.enviar(comprobante.venta_id).subscribe({
      next: (respuesta) => {
        this.enviando.set(false);
        if (respuesta.enviado) {
          this.toast.brand(respuesta.mensaje);
        } else {
          this.toast.error(respuesta.mensaje);
        }
      },
      error: (err) => {
        this.enviando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo enviar el comprobante. Inténtalo nuevamente.');
      },
    });
  }
}
