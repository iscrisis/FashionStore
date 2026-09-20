import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { Icon } from '../../../core/ui/icon/icon';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { CarritoItemOut, CarritoOut } from '../carrito.model';
import { CarritoService } from '../carrito.service';

/**
 * CU21 -- Usar carrito de compras (Cliente). Pantalla "Mi carrito"
 * ('/carrito', CLIENTE autenticado -- ver app.routes.ts).
 *
 * Diseño tipo tienda de ropa (no administrativo): tarjetas con imagen,
 * producto, color, talla, precio unitario ACTUAL y una selección individual
 * (checkbox) por unidad, más el subtotal de lo SELECCIONADO. Sin control de
 * cantidad -- cada item YA es una unidad concreta; agregar la misma variante
 * otra vez trae otra tarjeta independiente, nunca suma un contador (ver
 * agregar-carrito.ts). NO incluye todavía sucursal de retiro, dirección,
 * delivery, pago ni confirmar compra -- eso es CU22 en adelante, fuera de
 * este alcance (ver Models/carrito.py en el backend); "CONTINUAR COMPRA"
 * queda solo preparado visualmente, sin acción real todavía.
 *
 * Cada mutación (seleccionar, eliminar) llama al backend y reemplaza el
 * carrito completo con la respuesta -- nunca calcula el subtotal en el
 * cliente: el precio SIEMPRE es el que devuelve la API en ese momento.
 *
 * `formatearMonto` es la única puerta hacia `toFixed(2)`: el tipo
 * CarritoItemOut/CarritoOut declara `precio_unitario`/`subtotal_seleccionado`
 * como `number` (ver carrito.model.ts, y el fix de raíz en
 * CU21_UsarCarritoCompras/schemas.py -- esos campos ahora SIEMPRE viajan
 * como número JSON, nunca como string), pero un `interface` de TypeScript no
 * protege en tiempo de ejecución si el contrato llegara a romperse de nuevo:
 * `toFixed` solo se llama cuando el valor recibido es realmente un `number`
 * finito. Si no lo es, no se oculta el problema -- se deja constancia con
 * `console.error` (visible en DevTools) y la tarjeta muestra "--" en vez de
 * romper toda la pantalla del carrito.
 */
@Component({
  selector: 'app-mi-carrito',
  imports: [Icon, RouterLink],
  templateUrl: './mi-carrito.html',
  styleUrl: './mi-carrito.scss',
})
export class MiCarrito implements OnInit {
  private readonly service = inject(CarritoService);
  private readonly toast = inject(ToastService);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly cargando = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly carrito = signal<CarritoOut | null>(null);
  // item_id en curso (seleccionar o eliminar) -- deshabilita solo los
  // controles de ESA tarjeta mientras responde el backend, evita doble clic.
  protected readonly procesandoItemId = signal<number | null>(null);

  protected readonly haySeleccionados = computed(
    () => (this.carrito()?.items ?? []).some((item) => item.seleccionado),
  );

  ngOnInit(): void {
    this.cargar();
  }

  /** Único punto que llama `toFixed(2)` -- ver docstring de la clase. */
  protected formatearMonto(valor: unknown): string {
    if (typeof valor === 'number' && Number.isFinite(valor)) {
      return valor.toFixed(2);
    }
    // eslint-disable-next-line no-console -- a propósito, no se oculta el error.
    console.error('CU21 · Mi carrito: se esperaba un monto numérico y llegó', valor);
    return '--';
  }

  cargar(): void {
    this.cargando.set(true);
    this.errorMessage.set(null);
    this.service.consultar().subscribe({
      next: (carrito) => {
        this.carrito.set(carrito);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.errorMessage.set('No se pudo cargar tu carrito. Inténtalo nuevamente.');
      },
    });
  }

  toggleSeleccion(item: CarritoItemOut): void {
    if (this.procesandoItemId() !== null) {
      return;
    }
    this.procesandoItemId.set(item.item_id);
    this.service.actualizarSeleccion(item.item_id, { seleccionado: !item.seleccionado }).subscribe({
      next: (carrito) => {
        this.procesandoItemId.set(null);
        this.carrito.set(carrito);
      },
      error: () => {
        this.procesandoItemId.set(null);
        this.toast.error('No se pudo actualizar la selección. Inténtalo nuevamente.');
      },
    });
  }

  eliminar(item: CarritoItemOut): void {
    if (this.procesandoItemId() !== null) {
      return;
    }
    this.procesandoItemId.set(item.item_id);
    this.service.eliminarItem(item.item_id).subscribe({
      next: (carrito) => {
        this.procesandoItemId.set(null);
        this.carrito.set(carrito);
        this.toast.brand('Producto eliminado del carrito.');
      },
      error: (err) => {
        this.procesandoItemId.set(null);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo eliminar el producto. Inténtalo nuevamente.');
      },
    });
  }
}
