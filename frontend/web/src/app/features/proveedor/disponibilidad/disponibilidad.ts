import { Component, inject, signal } from '@angular/core';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { ProductoProveedor } from '../shared/panel-proveedor.model';
import { PanelProveedorService } from '../shared/panel-proveedor.service';

@Component({
  selector: 'app-disponibilidad',
  imports: [],
  templateUrl: './disponibilidad.html',
  styleUrl: './disponibilidad.scss',
})
export class Disponibilidad {
  private readonly panelService = inject(PanelProveedorService);
  private readonly toast = inject(ToastService);

  protected readonly productos = signal<ProductoProveedor[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly savingId = signal<number | null>(null);

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.panelService.misProductos().subscribe({
      next: (productos) => {
        this.productos.set(productos.filter((p) => p.is_active));
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.errorMessage.set(
          'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
        );
      },
    });
  }

  toggle(producto: ProductoProveedor): void {
    this.savingId.set(producto.id);
    this.panelService.cambiarDisponibilidad(producto.id, !producto.disponibilidad).subscribe({
      next: (actualizado) => {
        this.savingId.set(null);
        this.productos.update((lista) =>
          lista.map((p) => (p.id === actualizado.id ? actualizado : p)),
        );
        this.toast.success(
          actualizado.disponibilidad ? 'Marcado como disponible.' : 'Marcado como no disponible.',
        );
      },
      error: () => {
        this.savingId.set(null);
        this.toast.error('No se pudo actualizar la disponibilidad.');
      },
    });
  }
}
