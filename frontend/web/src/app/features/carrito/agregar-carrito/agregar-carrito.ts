import { Component, effect, inject, input, output, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { CarritoService } from '../carrito.service';

/**
 * CU21 -- Agregar al carrito, desde la ficha de producto (producto-detalle).
 *
 * Convive con CrearReserva (CU17, "Reservar") en la misma ficha, sin tocar
 * su lógica: agregar al carrito solo necesita una variante válida (color +
 * talla ya elegidos más arriba en producto-detalle.ts) -- a diferencia de
 * "Reservar", NUNCA pide ciudad, sucursal, fecha ni hora.
 *
 * Mismo patrón de intención pendiente que CrearReserva para visitantes sin
 * sesión, adaptado a una acción que se completa SOLA al volver (no reabre
 * ningún modal para un clic extra):
 *  - sin sesión: navega a /login con returnUrl (mismo returnUrl base que ya
 *    arma producto-detalle.ts para el carrito -- conserva talla/color) más
 *    `&agregarCarrito=1`;
 *  - `autoAgregarParam` (leído por producto-detalle.ts de ese mismo query
 *    param al volver) dispara el agregado UNA SOLA VEZ -- `intentoAplicado`
 *    lo evita dentro del mismo montaje del componente, y en cuanto se
 *    dispara (con éxito o con error) se limpia el query param de la URL
 *    (replaceUrl) para que un F5 posterior no lo vuelva a agregar.
 *
 * "Producto agregado al carrito." es un toast "brand" (rojo FashionStore),
 * mismo tipo que ya usa CU17 -- no mueve el layout ni bloquea la ficha.
 */
@Component({
  selector: 'app-agregar-carrito',
  imports: [Icon],
  templateUrl: './agregar-carrito.html',
  styleUrl: './agregar-carrito.scss',
})
export class AgregarCarrito {
  private readonly auth = inject(AuthService);
  private readonly service = inject(CarritoService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly productoVarianteId = input<number | null>(null);
  readonly returnUrl = input<string>('/');
  // Viene del returnUrl al volver del login (ver producto-detalle.ts) --
  // "1" crudo sin validar todavía, mismo criterio que fechaRestaurada/
  // horaRestaurada en crear-reserva.ts.
  readonly autoAgregarParam = input<boolean>(false);
  readonly agregado = output<void>();

  protected readonly isAuthenticated = this.auth.isAuthenticated;
  protected readonly submitting = signal(false);

  private intentoAplicado = false;

  constructor() {
    effect(() => {
      const variante = this.productoVarianteId();
      if (
        this.intentoAplicado ||
        !this.autoAgregarParam() ||
        variante === null ||
        !this.isAuthenticated() ||
        this.submitting()
      ) {
        return;
      }
      this.intentoAplicado = true;
      this._agregar(variante, true);
    });
  }

  protected get esCliente(): boolean {
    return this.auth.hasRole('CLIENTE');
  }

  protected get puedeAgregar(): boolean {
    return this.productoVarianteId() !== null && !this.submitting();
  }

  agregar(): void {
    if (!this.puedeAgregar) {
      return;
    }
    if (!this.isAuthenticated()) {
      const url = `${this.returnUrl()}&agregarCarrito=1`;
      this.router.navigate(['/login'], { queryParams: { returnUrl: url } });
      return;
    }
    this._agregar(this.productoVarianteId()!, false);
  }

  private _agregar(varianteId: number, esAutomatico: boolean): void {
    this.submitting.set(true);
    this.service.agregarItem({ producto_variante_id: varianteId }).subscribe({
      next: () => {
        this.submitting.set(false);
        this.toast.brand('Producto agregado al carrito.');
        if (esAutomatico) {
          this._limpiarFlagUrl();
        }
        this.agregado.emit();
      },
      error: (err) => {
        this.submitting.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo agregar el producto al carrito. Inténtalo nuevamente.');
        if (esAutomatico) {
          this._limpiarFlagUrl();
        }
      },
    });
  }

  // Quita "agregarCarrito" de la URL sin recargar ni perder el resto de los
  // query params (tallaId/colorId) -- evita que F5 dispare el efecto de
  // nuevo y agregue el producto otra vez.
  private _limpiarFlagUrl(): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { agregarCarrito: null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }
}
