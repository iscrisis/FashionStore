import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { CambiarModal } from './cambiar-modal/cambiar-modal';
import { DetalleDevolucionOut, MetodoPagoDevolucion, VentaDevolucionOut } from './devolucion-cambio.model';
import { DevolucionCambioService } from './devolucion-cambio.service';
import { DevolverModal } from './devolver-modal/devolver-modal';

/**
 * CU26 -- Registrar devolución o cambio (Cajero). Busca una Venta PAGADA
 * por `codigo_venta` (VT-XXXXX) -- NUNCA lista todas las ventas de todos los
 * Clientes, ver devolucion-cambio.service.ts -- y muestra únicamente las
 * líneas que todavía pueden devolverse/cambiarse (el backend ya filtra las
 * agotadas, ver CU26_RegistrarDevolucionCambio/service.py).
 *
 * "Devolver"/"Cambiar" abren una ficha modal sobre esta misma pantalla
 * (nunca navegan, mismo criterio que procesar-pago.ts, CU25). Al confirmar
 * cualquiera de las dos, se vuelve a pedir la misma Venta (mismo
 * `codigo_venta`) para reflejar el nuevo `cantidad_disponible` -- una
 * prenda ya completamente devuelta/cambiada simplemente deja de aparecer.
 *
 * CU27 (Historial del Cajero) "prepara" esta pantalla con el botón
 * "Devolución" de una fila de su historial, navegando aquí con
 * `?codigo=VT-XXXXX` -- este componente solo LEE ese query param al entrar
 * para precargar el buscador y disparar la búsqueda automáticamente, nunca
 * vuelve a implementar la devolución en sí (esa lógica sigue siendo,
 * enteramente, la de este mismo componente/CU26).
 */
@Component({
  selector: 'app-devoluciones-cambios',
  imports: [Icon, DevolverModal, CambiarModal],
  templateUrl: './devoluciones-cambios.html',
  styleUrl: './devoluciones-cambios.scss',
})
export class DevolucionesCambios implements OnInit {
  private readonly service = inject(DevolucionCambioService);
  private readonly route = inject(ActivatedRoute);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly codigo = signal('');
  protected readonly buscando = signal(false);
  protected readonly seBusco = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly venta = signal<VentaDevolucionOut | null>(null);

  protected readonly detalleParaDevolver = signal<DetalleDevolucionOut | null>(null);
  protected readonly detalleParaCambiar = signal<DetalleDevolucionOut | null>(null);

  ngOnInit(): void {
    const codigoPreparado = this.route.snapshot.queryParamMap.get('codigo');
    if (codigoPreparado) {
      this.codigo.set(codigoPreparado.toUpperCase());
      this.buscar();
    }
  }

  actualizarCodigo(valor: string): void {
    this.codigo.set(valor.toUpperCase());
  }

  buscar(): void {
    const codigo = this.codigo().trim();
    if (!codigo || this.buscando()) {
      return;
    }
    this.buscando.set(true);
    this.errorMessage.set(null);
    this.venta.set(null);
    this.service.buscarVenta(codigo).subscribe({
      next: (venta) => {
        this.buscando.set(false);
        this.seBusco.set(true);
        this.venta.set(venta);
      },
      error: (err) => {
        this.buscando.set(false);
        this.seBusco.set(true);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.errorMessage.set(detalle ?? 'No se pudo buscar la venta. Inténtalo nuevamente.');
      },
    });
  }

  abrirDevolver(detalle: DetalleDevolucionOut): void {
    this.detalleParaDevolver.set(detalle);
  }

  cerrarDevolver(): void {
    this.detalleParaDevolver.set(null);
  }

  abrirCambiar(detalle: DetalleDevolucionOut): void {
    this.detalleParaCambiar.set(detalle);
  }

  cerrarCambiar(): void {
    this.detalleParaCambiar.set(null);
  }

  onOperacionRegistrada(): void {
    this.detalleParaDevolver.set(null);
    this.detalleParaCambiar.set(null);
    const actual = this.venta();
    if (!actual) {
      return;
    }
    this.service.buscarVenta(actual.codigo_venta).subscribe({
      next: (venta) => this.venta.set(venta),
    });
  }

  protected etiquetaMetodo(metodo: MetodoPagoDevolucion): string {
    const etiquetas: Record<MetodoPagoDevolucion, string> = {
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
