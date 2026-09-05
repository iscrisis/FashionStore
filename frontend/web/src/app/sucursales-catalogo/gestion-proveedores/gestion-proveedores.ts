import { Component, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ConfirmDialogService } from '../../core/ui/confirm-dialog/confirm-dialog.service';
import { Icon } from '../../core/ui/icon/icon';
import { StatusBadge } from '../../core/ui/status-badge/status-badge';
import { ToastService } from '../../core/ui/toast/toast.service';
import { CatalogStatusFilter, Proveedor } from './proveedor.model';
import { ProveedorService } from './proveedor.service';
import { ProveedorForm, ProveedorFormValue } from './proveedor-form/proveedor-form';

@Component({
  selector: 'app-gestion-proveedores',
  imports: [FormsModule, Icon, StatusBadge, ProveedorForm],
  templateUrl: './gestion-proveedores.html',
  styleUrl: './gestion-proveedores.scss',
})
export class GestionProveedores {
  private readonly proveedorService = inject(ProveedorService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly proveedores = signal<Proveedor[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly searchTerm = signal('');
  protected readonly statusFilter = signal<CatalogStatusFilter>('all');

  protected readonly drawerOpen = signal(false);
  protected readonly editingProveedor = signal<Proveedor | null>(null);
  protected readonly viewMode = signal(false);
  protected readonly submitting = signal(false);

  protected readonly openMenuId = signal<number | null>(null);

  private searchDebounce?: ReturnType<typeof setTimeout>;

  constructor() {
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

  onStatusFilterChange(value: string): void {
    this.statusFilter.set(value as CatalogStatusFilter);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.proveedorService
      .list({ search: this.searchTerm() || undefined, estado: this.statusFilter() })
      .subscribe({
        next: (proveedores) => {
          this.proveedores.set(proveedores);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.proveedores.set([]);
          this.errorMessage.set(
            'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
          );
        },
      });
  }

  openCreate(): void {
    this.editingProveedor.set(null);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openEdit(proveedor: Proveedor): void {
    this.openMenuId.set(null);
    this.editingProveedor.set(proveedor);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openView(proveedor: Proveedor, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(null);
    this.editingProveedor.set(proveedor);
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

  save(payload: ProveedorFormValue): void {
    const editing = this.editingProveedor();
    this.submitting.set(true);

    if (editing) {
      const requests = [
        this.proveedorService.update(editing.id, {
          razon_social: payload.razon_social,
          nombre_contacto: payload.nombre_contacto,
          correo: payload.correo,
          telefono: payload.telefono,
        }),
      ];
      if (payload.is_active !== editing.is_active) {
        requests.push(this.proveedorService.setActive(editing.id, payload.is_active));
      }
      forkJoin(requests).subscribe({
        next: () => this.onSaveSuccess('Proveedor actualizado correctamente.'),
        error: (err) => this.onSaveError(err),
      });
      return;
    }

    this.proveedorService.create(payload).subscribe({
      next: () => this.onSaveSuccess('Proveedor creado correctamente.'),
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
      this.toast.error('Ya existe un proveedor con esa razón social.');
    } else if (err.status === 422) {
      this.toast.error('Revisa los datos ingresados: correo o teléfono no válidos.');
    } else {
      this.toast.error('No se pudo guardar el proveedor. Intenta nuevamente.');
    }
  }

  async toggleStatus(proveedor: Proveedor, event: Event): Promise<void> {
    event.stopPropagation();
    this.openMenuId.set(null);

    if (proveedor.is_active) {
      const confirmed = await this.confirmDialog.confirm({
        title: '¿Desactivar proveedor?',
        message: `${proveedor.razon_social} dejará de estar disponible para nuevas operaciones.`,
        confirmText: 'Desactivar',
        danger: true,
      });
      if (!confirmed) {
        return;
      }
    }

    this.proveedorService.setActive(proveedor.id, !proveedor.is_active).subscribe({
      next: () => {
        this.toast.success(
          proveedor.is_active ? 'Proveedor desactivado.' : 'Proveedor activado correctamente.',
        );
        this.load();
      },
      error: () => this.toast.error('No se pudo actualizar el estado del proveedor.'),
    });
  }
}
