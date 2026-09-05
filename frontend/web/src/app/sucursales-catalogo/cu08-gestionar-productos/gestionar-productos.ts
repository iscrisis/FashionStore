import { Component, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ConfirmDialogService } from '../../core/ui/confirm-dialog/confirm-dialog.service';
import { Icon } from '../../core/ui/icon/icon';
import { StatusBadge } from '../../core/ui/status-badge/status-badge';
import { ToastService } from '../../core/ui/toast/toast.service';
import { resolveMediaUrl } from '../../core/utils/resolve-media-url';
import { CategoryService } from '../atributos/services/category.service';
import { Category } from '../atributos/models/category.model';
import { TemporadaAdminService } from '../cu10-gestionar-temporadas-colecciones/temporada-admin.service';
import { Temporada } from '../cu10-gestionar-temporadas-colecciones/temporada-coleccion.model';
import { CatalogStatusFilter, Producto } from './producto.model';
import { ProductoService } from './producto.service';
import { ProductoForm, ProductoFormValue } from './producto-form/producto-form';

@Component({
  selector: 'app-gestionar-productos',
  imports: [FormsModule, Icon, StatusBadge, ProductoForm],
  templateUrl: './gestionar-productos.html',
  styleUrl: './gestionar-productos.scss',
})
export class GestionarProductos {
  protected readonly resolveMediaUrl = resolveMediaUrl;

  private readonly productoService = inject(ProductoService);
  private readonly categoryService = inject(CategoryService);
  private readonly temporadaService = inject(TemporadaAdminService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly productos = signal<Producto[]>([]);
  protected readonly categorias = signal<Category[]>([]);
  protected readonly temporadas = signal<Temporada[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly searchTerm = signal('');
  protected readonly categoriaFilter = signal<number | null>(null);
  protected readonly temporadaFilter = signal<number | null>(null);
  protected readonly statusFilter = signal<CatalogStatusFilter>('all');

  protected readonly drawerOpen = signal(false);
  protected readonly editingProducto = signal<Producto | null>(null);
  protected readonly viewMode = signal(false);
  protected readonly submitting = signal(false);

  protected readonly openMenuId = signal<number | null>(null);

  private searchDebounce?: ReturnType<typeof setTimeout>;

  constructor() {
    this.categoryService.list().subscribe((categorias) => this.categorias.set(categorias));
    this.temporadaService.list().subscribe((temporadas) => this.temporadas.set(temporadas));
    this.load();
  }

  @HostListener('document:click')
  closeMenus(): void {
    this.openMenuId.set(null);
  }

  onSearchChange(value: string): void {
    this.searchTerm.set(value);
    clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => this.load(), 350);
  }

  onCategoriaFilterChange(value: string): void {
    this.categoriaFilter.set(value ? Number(value) : null);
    this.load();
  }

  onTemporadaFilterChange(value: string): void {
    this.temporadaFilter.set(value ? Number(value) : null);
    this.load();
  }

  onStatusFilterChange(value: string): void {
    this.statusFilter.set(value as CatalogStatusFilter);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.productoService
      .list({
        search: this.searchTerm() || undefined,
        categoria_id: this.categoriaFilter() ?? undefined,
        temporada_id: this.temporadaFilter() ?? undefined,
        estado: this.statusFilter(),
      })
      .subscribe({
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

  openCreate(): void {
    this.editingProducto.set(null);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openEdit(producto: Producto): void {
    this.openMenuId.set(null);
    this.editingProducto.set(producto);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openView(producto: Producto, event: Event): void {
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

  save(payload: ProductoFormValue): void {
    const editing = this.editingProducto();
    this.submitting.set(true);

    if (editing) {
      const requests = [this.productoService.update(editing.id, payload)];
      if (payload.is_active !== editing.is_active) {
        requests.push(this.productoService.setActive(editing.id, payload.is_active ?? true));
      }
      forkJoin(requests).subscribe({
        next: () => this.onSaveSuccess('Producto actualizado correctamente.'),
        error: (err) => this.onSaveError(err),
      });
      return;
    }

    this.productoService.create(payload).subscribe({
      next: (creado) => {
        this.submitting.set(false);
        this.editingProducto.set(creado);
        this.toast.success('Producto creado. Ahora puedes cargar su imagen principal.');
        this.load();
      },
      error: (err) => this.onSaveError(err),
    });
  }

  private onSaveSuccess(message: string): void {
    this.submitting.set(false);
    this.drawerOpen.set(false);
    this.toast.success(message);
    this.load();
  }

  private onSaveError(err: { status?: number }): void {
    this.submitting.set(false);
    if (err.status === 409) {
      this.toast.error('Esa propuesta ya fue convertida en un producto.');
    } else if (err.status === 422) {
      this.toast.error('Revisa los datos ingresados: alguna referencia seleccionada no es válida.');
    } else {
      this.toast.error('No se pudo guardar el producto. Intenta nuevamente.');
    }
  }

  async toggleStatus(producto: Producto, event: Event): Promise<void> {
    event.stopPropagation();
    this.openMenuId.set(null);

    if (producto.is_active) {
      const confirmed = await this.confirmDialog.confirm({
        title: '¿Desactivar producto?',
        message: `${producto.nombre} dejará de estar disponible en el catálogo.`,
        confirmText: 'Desactivar',
        danger: true,
      });
      if (!confirmed) {
        return;
      }
    }

    this.productoService.setActive(producto.id, !producto.is_active).subscribe({
      next: () => {
        this.toast.success(
          producto.is_active ? 'Producto desactivado.' : 'Producto activado correctamente.',
        );
        this.load();
      },
      error: () => this.toast.error('No se pudo actualizar el estado del producto.'),
    });
  }
}
