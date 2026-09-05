import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { Icon } from '../../../core/ui/icon/icon';
import { ProductoProveedor } from '../shared/panel-proveedor.model';
import { PanelProveedorService } from '../shared/panel-proveedor.service';

@Component({
  selector: 'app-proveedor-inicio',
  imports: [RouterLink, Icon],
  templateUrl: './inicio.html',
  styleUrl: './inicio.scss',
})
export class Inicio {
  private readonly panelService = inject(PanelProveedorService);
  private readonly authService = inject(AuthService);

  protected readonly usuario = this.authService.usuario;
  protected readonly productos = signal<ProductoProveedor[]>([]);
  protected readonly loading = signal(true);

  protected readonly totalProductos = computed(() => this.productos().length);
  protected readonly disponibles = computed(
    () => this.productos().filter((p) => p.disponibilidad).length,
  );
  protected readonly activos = computed(() => this.productos().filter((p) => p.is_active).length);

  constructor() {
    this.panelService.misProductos().subscribe({
      next: (productos) => {
        this.productos.set(productos);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
