import { Component, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ConfirmDialogService } from '../../core/ui/confirm-dialog/confirm-dialog.service';
import { Icon } from '../../core/ui/icon/icon';
import { StatusBadge } from '../../core/ui/status-badge/status-badge';
import { ToastService } from '../../core/ui/toast/toast.service';
import { CiudadManagement } from './ciudad-management/ciudad-management';
import { CatalogStatusFilter, Ciudad, SucursalAdmin } from './sucursal-admin.model';
import { SucursalAdminService } from './sucursal-admin.service';
import { SucursalForm, SucursalFormValue } from './sucursal-form/sucursal-form';

@Component({
  selector: 'app-sucursales',
  imports: [FormsModule, Icon, StatusBadge, SucursalForm, CiudadManagement],
  templateUrl: './sucursales.html',
  styleUrl: './sucursales.scss',
})
export class Sucursales {
  private readonly sucursalService = inject(SucursalAdminService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly sucursales = signal<SucursalAdmin[]>([]);
  protected readonly ciudades = signal<Ciudad[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly searchTerm = signal('');
  protected readonly ciudadFilter = signal<number | ''>('');
  protected readonly statusFilter = signal<CatalogStatusFilter>('all');

  protected readonly drawerOpen = signal(false);
  protected readonly editingSucursal = signal<SucursalAdmin | null>(null);
  protected readonly viewMode = signal(false);
  protected readonly submitting = signal(false);

  protected readonly openMenuId = signal<number | null>(null);
  protected readonly cityManagementOpen = signal(false);

  private searchDebounce?: ReturnType<typeof setTimeout>;

  constructor() {
    this.loadCiudades();
    this.load();
  }

  protected loadCiudades(): void {
    this.sucursalService
      .ciudades('active')
      .subscribe({ next: (ciudades) => this.ciudades.set(ciudades) });
  }

  openCityManagement(): void {
    this.cityManagementOpen.set(true);
  }

  closeCityManagement(): void {
    this.cityManagementOpen.set(false);
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

  onCiudadFilterChange(value: string): void {
    this.ciudadFilter.set(value ? Number(value) : '');
    this.load();
  }

  onStatusFilterChange(value: string): void {
    this.statusFilter.set(value as CatalogStatusFilter);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.sucursalService
      .list({
        search: this.searchTerm() || undefined,
        ciudad_id: this.ciudadFilter() || undefined,
        estado: this.statusFilter(),
      })
      .subscribe({
        next: (sucursales) => {
          this.sucursales.set(sucursales);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.sucursales.set([]);
          this.errorMessage.set(
            'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
          );
        },
      });
  }

  openCreate(): void {
    this.editingSucursal.set(null);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openEdit(sucursal: SucursalAdmin): void {
    this.openMenuId.set(null);
    this.editingSucursal.set(sucursal);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openView(sucursal: SucursalAdmin, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(null);
    this.editingSucursal.set(sucursal);
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

  save(payload: SucursalFormValue): void {
    const editing = this.editingSucursal();
    this.submitting.set(true);

    if (editing) {
      const requests = [
        this.sucursalService.update(editing.id, {
          nombre: payload.nombre,
          ciudad_id: payload.ciudad_id,
          direccion: payload.direccion,
          telefono: payload.telefono,
        }),
      ];
      if (payload.is_active !== editing.is_active) {
        requests.push(this.sucursalService.setActive(editing.id, payload.is_active));
      }
      forkJoin(requests).subscribe({
        next: () => this.onSaveSuccess('Sucursal actualizada correctamente.'),
        error: (err) => this.onSaveError(err),
      });
      return;
    }

    this.sucursalService.create(payload).subscribe({
      next: () => this.onSaveSuccess('Sucursal creada correctamente.'),
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
      this.toast.error('Ya existe una sucursal con ese nombre en esa ciudad.');
    } else if (err.status === 422) {
      this.toast.error('La ciudad seleccionada no es válida.');
    } else {
      this.toast.error('No se pudo guardar la sucursal. Intenta nuevamente.');
    }
  }

  async toggleStatus(sucursal: SucursalAdmin, event: Event): Promise<void> {
    event.stopPropagation();
    this.openMenuId.set(null);

    if (sucursal.is_active) {
      const confirmed = await this.confirmDialog.confirm({
        title: '¿Desactivar sucursal?',
        message: `${sucursal.nombre} dejará de estar disponible para operar.`,
        confirmText: 'Desactivar',
        danger: true,
      });
      if (!confirmed) {
        return;
      }
    }

    this.sucursalService.setActive(sucursal.id, !sucursal.is_active).subscribe({
      next: () => {
        this.toast.success(
          sucursal.is_active ? 'Sucursal desactivada.' : 'Sucursal activada correctamente.',
        );
        this.load();
      },
      error: () => {
        this.toast.error('No se pudo actualizar el estado de la sucursal.');
      },
    });
  }
}
