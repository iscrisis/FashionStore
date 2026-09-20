import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { PagoElectronicoService } from '../pago-electronico.service';

/**
 * CU23 -- Procesar pago electrónico (Cliente). Punto de entrada hacia
 * Stripe ('/pago/iniciar?venta_id=X', CLIENTE autenticado -- ver
 * app.routes.ts), al que navega CU22 apenas confirma la Venta
 * (PENDIENTE_PAGO) -- ver features/compra-digital/finalizar-compra/finalizar-compra.ts.
 *
 * Al montarse, pide a FastAPI una Checkout Session para `venta_id` (que
 * vuelve a validar propietario, tipo, estado y disponibilidad -- ver
 * CU23_ProcesarPagoElectronico/service.py) y, apenas recibe la URL segura de
 * Stripe, redirige el navegador ahí EN LA MISMA PESTAÑA
 * (`window.location.href`, nunca `window.open`) -- Angular no arma ningún
 * formulario de tarjeta: Stripe Checkout Hosted se encarga de toda esa
 * pantalla.
 *
 * Si la Venta ya no admite pago (p. ej. el stock cambió entre CU22 y este
 * paso), se muestra un estado de error amigable con salida al carrito --
 * nunca el detalle técnico que devuelva el backend sin filtrar.
 */
@Component({
  selector: 'app-iniciar-pago',
  imports: [RouterLink],
  templateUrl: './iniciar-pago.html',
  styleUrl: './iniciar-pago.scss',
})
export class IniciarPago implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(PagoElectronicoService);

  protected readonly errorMessage = signal<string | null>(null);
  protected readonly ventaId = signal<number | null>(null);

  ngOnInit(): void {
    const idParam = this.route.snapshot.queryParamMap.get('venta_id');
    const ventaId = idParam ? Number(idParam) : null;
    if (!ventaId) {
      this.errorMessage.set('No se encontró la compra a pagar.');
      return;
    }
    this.ventaId.set(ventaId);
    this._iniciarCheckout(ventaId);
  }

  reintentar(): void {
    const ventaId = this.ventaId();
    if (!ventaId) {
      return;
    }
    this.errorMessage.set(null);
    this._iniciarCheckout(ventaId);
  }

  private _iniciarCheckout(ventaId: number): void {
    this.service.crearCheckout({ venta_id: ventaId }).subscribe({
      next: (sesion) => {
        // Redirige EN LA MISMA pestaña -- nunca un popup ni una nueva.
        window.location.href = sesion.checkout_url;
      },
      error: (err) => {
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.errorMessage.set(detalle ?? 'No se pudo iniciar el pago. Inténtalo nuevamente.');
      },
    });
  }
}
