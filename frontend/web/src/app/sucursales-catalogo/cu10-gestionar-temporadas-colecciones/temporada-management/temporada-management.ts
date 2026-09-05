import { DatePipe } from '@angular/common';
import { Component, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CatalogStatusFilter, Temporada, TemporadaPayload } from '../temporada-coleccion.model';
import { TemporadaAdminService } from '../temporada-admin.service';
import { ConfirmDialogService } from '../../../core/ui/confirm-dialog/confirm-dialog.service';
import { Icon } from '../../../core/ui/icon/icon';
import { StatusBadge } from '../../../core/ui/status-badge/status-badge';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { TemporadaForm } from './temporada-form/temporada-form';

@Component({
  selector: 'app-temporada-management',
  imports: [FormsModule, DatePipe, Icon, StatusBadge, TemporadaForm],
  templateUrl: './temporada-management.html',
  styleUrl: './temporada-management.scss',
})
export class TemporadaManagement {
  private readonly temporadaService = inject(TemporadaAdminService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly temporadas = signal<Temporada[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly searchTerm = signal('');
  protected readonly statusFilter = signal<CatalogStatusFilter>('all');

  protected readonly drawerOpen = signal(false);
  protected readonly editingTemporada = signal<Temporada | null>(null);
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
    this.temporadaService
      .list({ search: this.searchTerm() || undefined, estado: this.statusFilter() })
      .subscribe({
        next: (temporadas) => {
          this.temporadas.set(temporadas);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.temporadas.set([]);
          this.errorMessage.set(
            'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
          );
        },
      });
  }

  openCreate(): void {
    this.editingTemporada.set(null);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openEdit(temporada: Temporada): void {
    this.openMenuId.set(null);
    this.editingTemporada.set(temporada);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openView(temporada: Temporada, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(null);
    this.editingTemporada.set(temporada);
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

  save(payload: TemporadaPayload): void {
    const editing = this.editingTemporada();
    this.submitting.set(true);
    const request$ = editing
      ? this.temporadaService.update(editing.id, payload)
      : this.temporadaService.create(payload);

    request$.subscribe({
      next: () => {
        this.submitting.set(false);
        this.drawerOpen.set(false);
        this.toast.success(
          editing ? 'Temporada actualizada correctamente.' : 'Temporada creada correctamente.',
        );
        this.load();
      },
      error: (err) => {
        this.submitting.set(false);
        if (err.status === 409) {
          this.toast.error('Ya existe una temporada con ese nombre.');
        } else {
          this.toast.error('No se pudo guardar la temporada. Intenta nuevamente.');
        }
      },
    });
  }

  async toggleStatus(temporada: Temporada, event: Event): Promise<void> {
    event.stopPropagation();
    this.openMenuId.set(null);

    if (temporada.is_active) {
      const confirmed = await this.confirmDialog.confirm({
        title: '¿Desactivar temporada?',
        message: 'La temporada y sus colecciones dejarán de mostrarse como disponibles.',
        confirmText: 'Desactivar',
        danger: true,
      });
      if (!confirmed) {
        return;
      }
    }

    this.temporadaService.setActive(temporada.id, !temporada.is_active).subscribe({
      next: () => {
        this.toast.success(
          temporada.is_active ? 'Temporada desactivada.' : 'Temporada activada correctamente.',
        );
        this.load();
      },
      error: () => this.toast.error('No se pudo actualizar el estado de la temporada.'),
    });
  }
}
