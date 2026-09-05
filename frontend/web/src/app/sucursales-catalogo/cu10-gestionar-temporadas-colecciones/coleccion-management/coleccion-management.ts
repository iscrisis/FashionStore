import { Component, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Coleccion, ColeccionPayload, CatalogStatusFilter, Temporada } from '../temporada-coleccion.model';
import { ColeccionAdminService } from '../coleccion-admin.service';
import { TemporadaAdminService } from '../temporada-admin.service';
import { ConfirmDialogService } from '../../../core/ui/confirm-dialog/confirm-dialog.service';
import { Icon } from '../../../core/ui/icon/icon';
import { StatusBadge } from '../../../core/ui/status-badge/status-badge';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { ColeccionForm } from './coleccion-form/coleccion-form';

@Component({
  selector: 'app-coleccion-management',
  imports: [FormsModule, Icon, StatusBadge, ColeccionForm],
  templateUrl: './coleccion-management.html',
  styleUrl: './coleccion-management.scss',
})
export class ColeccionManagement {
  private readonly coleccionService = inject(ColeccionAdminService);
  private readonly temporadaService = inject(TemporadaAdminService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly colecciones = signal<Coleccion[]>([]);
  protected readonly temporadas = signal<Temporada[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly searchTerm = signal('');
  protected readonly temporadaFilter = signal<number | ''>('');
  protected readonly statusFilter = signal<CatalogStatusFilter>('all');

  protected readonly drawerOpen = signal(false);
  protected readonly editingColeccion = signal<Coleccion | null>(null);
  protected readonly viewMode = signal(false);
  protected readonly submitting = signal(false);

  protected readonly openMenuId = signal<number | null>(null);

  private searchDebounce?: ReturnType<typeof setTimeout>;

  constructor() {
    this.temporadaService.list({ estado: 'active' }).subscribe({
      next: (temporadas) => this.temporadas.set(temporadas),
    });
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

  onTemporadaFilterChange(value: string): void {
    this.temporadaFilter.set(value ? Number(value) : '');
    this.load();
  }

  onStatusFilterChange(value: string): void {
    this.statusFilter.set(value as CatalogStatusFilter);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.coleccionService
      .list({
        search: this.searchTerm() || undefined,
        temporada_id: this.temporadaFilter() || undefined,
        estado: this.statusFilter(),
      })
      .subscribe({
        next: (colecciones) => {
          this.colecciones.set(colecciones);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.colecciones.set([]);
          this.errorMessage.set(
            'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
          );
        },
      });
  }

  openCreate(): void {
    this.editingColeccion.set(null);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openEdit(coleccion: Coleccion): void {
    this.openMenuId.set(null);
    this.editingColeccion.set(coleccion);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openView(coleccion: Coleccion, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(null);
    this.editingColeccion.set(coleccion);
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

  save(payload: ColeccionPayload): void {
    const editing = this.editingColeccion();
    this.submitting.set(true);
    const request$ = editing
      ? this.coleccionService.update(editing.id, payload)
      : this.coleccionService.create(payload);

    request$.subscribe({
      next: () => {
        this.submitting.set(false);
        this.drawerOpen.set(false);
        this.toast.success(
          editing ? 'Colección actualizada correctamente.' : 'Colección creada correctamente.',
        );
        this.load();
      },
      error: (err) => {
        this.submitting.set(false);
        if (err.status === 409) {
          this.toast.error('Ya existe una colección con ese nombre en esa temporada.');
        } else if (err.status === 422) {
          this.toast.error('La temporada seleccionada no es válida.');
        } else {
          this.toast.error('No se pudo guardar la colección. Intenta nuevamente.');
        }
      },
    });
  }

  async toggleStatus(coleccion: Coleccion, event: Event): Promise<void> {
    event.stopPropagation();
    this.openMenuId.set(null);

    if (coleccion.is_active) {
      const confirmed = await this.confirmDialog.confirm({
        title: '¿Desactivar colección?',
        message: 'La colección dejará de estar disponible para nuevos productos.',
        confirmText: 'Desactivar',
        danger: true,
      });
      if (!confirmed) {
        return;
      }
    }

    this.coleccionService.setActive(coleccion.id, !coleccion.is_active).subscribe({
      next: () => {
        this.toast.success(
          coleccion.is_active ? 'Colección desactivada.' : 'Colección activada correctamente.',
        );
        this.load();
      },
      error: () => this.toast.error('No se pudo actualizar el estado de la colección.'),
    });
  }
}
