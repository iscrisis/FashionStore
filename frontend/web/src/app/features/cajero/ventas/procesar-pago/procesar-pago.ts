import { Component, computed, inject, input, output, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Icon } from '../../../../core/ui/icon/icon';
import { ToastService } from '../../../../core/ui/toast/toast.service';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { ComprobanteService, descargarBlob } from '../../../comprobantes/comprobante.service';
import {
  ConfirmarPagoPayload,
  MetodoPago,
  PagoConfirmadoOut,
  TipoTarjeta,
  VentaPresencialOut,
} from '../venta-presencial.model';
import { VentaPresencialService } from '../venta-presencial.service';

type Paso = 'formulario' | 'confirmado';

/**
 * CU25 -- Procesar pago presencial (Cajero). Ficha flotante/modal (NUNCA
 * navega a otra página) centrada sobre la pantalla actual, con el fondo
 * oscurecido -- ver procesar-pago.html/.scss.
 *
 * Componente ÚNICO, reutilizado por los dos puntos de entrada (nunca
 * duplicado):
 *  - "Cargar venta" en una tarjeta RS-XXXXX de reservas-pendientes.html
 *    (venta ORIGEN=RESERVA, ya creada/reutilizada por CU24 antes de abrir
 *    este modal).
 *  - "Continuar al pago" del resumen de venta directa
 *    (venta-resumen.html, ORIGEN=DIRECTA).
 *
 * Recibe la Venta YA armada por CU24 (`venta`, con sus detalles/total) como
 * input -- este modal nunca la crea ni la recalcula, solo la muestra y
 * cobra sobre ella. Tres métodos (EFECTIVO/TARJETA/QR) como tarjetas
 * grandes seleccionables; al elegir una, se revelan SUS campos propios
 * dentro del mismo modal (nunca un paso/pantalla aparte). "Confirmar pago"
 * llama a CU25; FastAPI vuelve a validar todo (monto, disponibilidad,
 * estado) -- este componente nunca decide que el pago es válido, solo
 * arma la solicitud y muestra el resultado.
 *
 * Cerrar el modal SIN confirmar (`cerrar`) no cambia nada: la Venta sigue
 * PENDIENTE_PAGO, lista para reabrirse sin duplicar nada (el padre decide
 * qué hacer con `cerrar`/`pagoRegistrado`, este componente no navega por
 * sí mismo).
 */
@Component({
  selector: 'app-procesar-pago',
  imports: [Icon],
  templateUrl: './procesar-pago.html',
  styleUrl: './procesar-pago.scss',
})
export class ProcesarPago {
  private readonly service = inject(VentaPresencialService);
  private readonly toast = inject(ToastService);
  private readonly comprobanteService = inject(ComprobanteService);
  private readonly router = inject(Router);

  readonly venta = input.required<VentaPresencialOut>();
  readonly cerrar = output<void>();
  readonly pagoRegistrado = output<void>();
  readonly nuevaVenta = output<void>();

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly paso = signal<Paso>('formulario');
  protected readonly metodoSeleccionado = signal<MetodoPago | null>(null);

  protected readonly montoRecibidoTexto = signal('');
  protected readonly tipoTarjeta = signal<TipoTarjeta | null>(null);
  protected readonly referencia = signal('');

  protected readonly confirmando = signal(false);
  protected readonly pagoConfirmado = signal<PagoConfirmadoOut | null>(null);

  // CU31 -- Emitir comprobante de venta. "Enviar" solo tiene sentido si la
  // venta tiene un Cliente registrado -- eso SOLO ocurre cuando viene de una
  // Reserva (CU24 nunca guarda cliente_id en una venta directa de
  // mostrador, ver CU24_RegistrarVentaPresencial/service.py), mismo dato ya
  // disponible en `venta().reserva`, sin pedir nada nuevo al backend.
  protected readonly tieneClienteRegistrado = computed(() => this.venta().reserva !== null);
  protected readonly descargandoComprobante = signal(false);
  protected readonly enviandoComprobante = signal(false);

  protected readonly montoRecibidoNumero = computed(() => {
    const valor = Number(this.montoRecibidoTexto().replace(',', '.'));
    return Number.isFinite(valor) ? valor : 0;
  });

  protected readonly cambio = computed(() => {
    const recibido = this.montoRecibidoNumero();
    const total = this.venta().total;
    return recibido >= total ? recibido - total : 0;
  });

  protected readonly puedeConfirmar = computed(() => {
    if (this.confirmando()) {
      return false;
    }
    const metodo = this.metodoSeleccionado();
    if (metodo === 'EFECTIVO') {
      return this.montoRecibidoNumero() >= this.venta().total;
    }
    if (metodo === 'TARJETA') {
      return this.tipoTarjeta() !== null;
    }
    return metodo === 'QR';
  });

  seleccionarMetodo(metodo: MetodoPago): void {
    this.metodoSeleccionado.set(metodo);
  }

  actualizarMontoRecibido(valor: string): void {
    this.montoRecibidoTexto.set(valor);
  }

  seleccionarTipoTarjeta(tipo: TipoTarjeta): void {
    this.tipoTarjeta.set(tipo);
  }

  actualizarReferencia(valor: string): void {
    this.referencia.set(valor);
  }

  confirmarPago(): void {
    const metodo = this.metodoSeleccionado();
    if (!metodo || !this.puedeConfirmar()) {
      return;
    }

    let payload: ConfirmarPagoPayload;
    if (metodo === 'EFECTIVO') {
      payload = { metodo_pago: 'EFECTIVO', monto_recibido: this.montoRecibidoNumero() };
    } else if (metodo === 'TARJETA') {
      const referencia = this.referencia().trim();
      payload = {
        metodo_pago: 'TARJETA',
        tipo_tarjeta: this.tipoTarjeta()!,
        ...(referencia ? { referencia } : {}),
      };
    } else {
      const referencia = this.referencia().trim();
      payload = { metodo_pago: 'QR', ...(referencia ? { referencia } : {}) };
    }

    this.confirmando.set(true);
    this.service.confirmarPago(this.venta().id, payload).subscribe({
      next: (pago) => {
        this.confirmando.set(false);
        this.pagoConfirmado.set(pago);
        this.paso.set('confirmado');
        this.pagoRegistrado.emit();
      },
      error: (err) => {
        this.confirmando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo registrar el pago. Inténtalo nuevamente.');
      },
    });
  }

  onCerrar(): void {
    if (this.confirmando()) {
      return;
    }
    this.cerrar.emit();
  }

  onNuevaVenta(): void {
    this.nuevaVenta.emit();
  }

  protected etiquetaMetodo(metodo: string): string {
    const etiquetas: Record<string, string> = { EFECTIVO: 'Efectivo', TARJETA: 'Tarjeta', QR: 'QR' };
    return etiquetas[metodo] ?? metodo;
  }

  verComprobante(): void {
    this.router.navigateByUrl(`/cajero/comprobante/${this.venta().id}`);
  }

  descargarComprobante(): void {
    if (this.descargandoComprobante()) {
      return;
    }
    const ventaId = this.venta().id;
    const codigoVenta = this.pagoConfirmado()?.codigo_venta ?? this.venta().codigo_venta;
    this.descargandoComprobante.set(true);
    this.comprobanteService.descargarPdf(ventaId).subscribe({
      next: (blob) => {
        this.descargandoComprobante.set(false);
        descargarBlob(blob, `${codigoVenta}.pdf`);
      },
      error: () => {
        this.descargandoComprobante.set(false);
        this.toast.error('No se pudo descargar el comprobante. Inténtalo nuevamente.');
      },
    });
  }

  enviarComprobante(): void {
    if (this.enviandoComprobante()) {
      return;
    }
    this.enviandoComprobante.set(true);
    this.comprobanteService.enviar(this.venta().id).subscribe({
      next: (respuesta) => {
        this.enviandoComprobante.set(false);
        if (respuesta.enviado) {
          this.toast.brand(respuesta.mensaje);
        } else {
          this.toast.error(respuesta.mensaje);
        }
      },
      error: (err) => {
        this.enviandoComprobante.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo enviar el comprobante. Inténtalo nuevamente.');
      },
    });
  }
}
