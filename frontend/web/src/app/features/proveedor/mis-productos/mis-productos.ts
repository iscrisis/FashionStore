import { Component, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Icon } from '../../../core/ui/icon/icon';
import { StatusBadge } from '../../../core/ui/status-badge/status-badge';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { ConfirmDialogService } from '../../../core/ui/confirm-dialog/confirm-dialog.service';
import { ProductoProveedor, ProductoProveedorPayload } from '../shared/panel-proveedor.model';
import { PanelProveedorService } from '../shared/panel-proveedor.service';
import { ProductoEditarForm } from './producto-editar-form/producto-editar-form';

type EstadoFiltro = 'all' | 'active' | 'inactive';

@Component({
  selector: 'app-mis-productos',
  imports: [FormsModule, Icon, StatusBadge, ProductoEditarForm],
  templateUrl: './mis-productos.html',
  styleUrl: './mis-productos.scss',
})
export class MisProductos {
  private readonly panelService = inject(PanelProveedorService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly productos = signal<ProductoProveedor[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly statusFilter = signal<EstadoFiltro>('all');

  protected readonly drawerOpen = signal(false);
  protected readonly editingProducto = signal<ProductoProveedor | null>(null);
  protected readonly viewMode = signal(false);
  protected readonly submitting = signal(false);

  protected readonly openMenuId = signal<number | null>(null);

  constructor() {
    this.load();
  }

  @HostListener('document:click')
  closeMenus(): void {
    this.openMenuId.set(null);
  }

  protected get productosFiltrados(): ProductoProveedor[] {
    const estado = this.statusFilter();
    if (estado === 'all') {
      return this.productos();
    }
    const activo = estado === 'active';
    return this.productos().filter((p) => p.is_active === activo);
  }

  onStatusFilterChange(value: string): void {
    this.statusFilter.set(value as EstadoFiltro);
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.panelService.misProductos().subscribe({
      next: (productos) => {
        this.productos.set(productos);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.productos.set([]);
        this.errorMessage.set(
          'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
        );
      },
    });
  }

  openEdit(producto: ProductoProveedor): void {
    this.openMenuId.set(null);
    this.editingProducto.set(producto);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openView(producto: ProductoProveedor, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(null);
    this.editingProducto.set(producto);
    this.viewMode.set(true);
    this.drawerOpen.set(true);
  }

  closeDrawer(): void {
    this.drawerOpen.set(false);
  }

  toggleMenu(id: number, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(this.openMenuId() === id ? null : id);
  }

  save(payload: ProductoProveedorPayload): void {
    const editing = this.editingProducto();
    if (!editing) {
      return;
    }
    this.submitting.set(true);
    this.panelService.actualizarProducto(editing.id, payload).subscribe({
      next: () => {
        this.submitting.set(false);
        this.drawerOpen.set(false);
        this.toast.success('Producto actualizado correctamente.');
        this.load();
      },
      error: (err) => {
        this.submitting.set(false);
        if (err.status === 422) {
          this.toast.error('Revisa la temporada y la colección seleccionadas.');
        } else {
          this.toast.error('No se pudo guardar el producto. Intenta nuevamente.');
        }
      },
    });
  }

  async toggleStatus(producto: ProductoProveedor, event: Event): Promise<void> {
    event.stopPropagation();
    this.openMenuId.set(null);

    if (producto.is_active) {
      const confirmed = await this.confirmDialog.confirm({
        title: '¿Desactivar producto?',
        message: `${producto.nombre} dejará de mostrarse como enviado.`,
        confirmText: 'Desactivar',
        danger: true,
      });
      if (!confirmed) {
        return;
      }
    }

    this.panelService.cambiarEstado(producto.id, !producto.is_active).subscribe({
      next: () => {
        this.toast.success(producto.is_active ? 'Producto desactivado.' : 'Producto activado correctamente.');
        this.load();
      },
      error: () => this.toast.error('No se pudo actualizar el estado del producto.'),
    });
  }
}
