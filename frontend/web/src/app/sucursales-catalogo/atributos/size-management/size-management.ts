import { Component, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CatalogStatusFilter } from '../models/catalog-status-filter.model';
import { Size, SizePayload } from '../models/size.model';
import { SizeService } from '../services/size.service';
import { ConfirmDialogService } from '../../../core/ui/confirm-dialog/confirm-dialog.service';
import { Icon } from '../../../core/ui/icon/icon';
import { StatusBadge } from '../../../core/ui/status-badge/status-badge';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { SizeForm } from './size-form/size-form';

@Component({
  selector: 'app-size-management',
  imports: [FormsModule, Icon, StatusBadge, SizeForm],
  templateUrl: './size-management.html',
  styleUrl: './size-management.scss',
})
export class SizeManagement {
  private readonly sizeService = inject(SizeService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly sizes = signal<Size[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly searchTerm = signal('');
  protected readonly statusFilter = signal<CatalogStatusFilter>('all');

  protected readonly drawerOpen = signal(false);
  protected readonly editingSize = signal<Size | null>(null);
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
    this.sizeService
      .list({ search: this.searchTerm() || undefined, estado: this.statusFilter() })
      .subscribe({
        next: (sizes) => {
          this.sizes.set(sizes);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.sizes.set([]);
          this.errorMessage.set(
            'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
          );
        },
      });
  }

  openCreate(): void {
    this.editingSize.set(null);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openEdit(size: Size): void {
    this.openMenuId.set(null);
    this.editingSize.set(size);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openView(size: Size, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(null);
    this.editingSize.set(size);
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

  save(payload: SizePayload): void {
    const editing = this.editingSize();
    this.submitting.set(true);
    const request$ = editing
      ? this.sizeService.update(editing.id, payload)
      : this.sizeService.create(payload);

    request$.subscribe({
      next: () => {
        this.submitting.set(false);
        this.drawerOpen.set(false);
        this.toast.success(editing ? 'Talla actualizada correctamente.' : 'Talla creada correctamente.');
        this.load();
      },
      error: (err) => {
        this.submitting.set(false);
        if (err.status === 409) {
          this.toast.error('Ya existe una talla con ese nombre.');
        } else {
          this.toast.error('No se pudo guardar la talla. Intenta nuevamente.');
        }
      },
    });
  }

  async toggleStatus(size: Size, event: Event): Promise<void> {
    event.stopPropagation();
    this.openMenuId.set(null);

    if (size.is_active) {
      const confirmed = await this.confirmDialog.confirm({
        title: '¿Desactivar talla?',
        message: 'La talla dejará de estar disponible para nuevas prendas.',
        confirmText: 'Desactivar',
        danger: true,
      });
      if (!confirmed) {
        return;
      }
    }

    this.sizeService.setActive(size.id, !size.is_active).subscribe({
      next: () => {
        this.toast.success(size.is_active ? 'Talla desactivada.' : 'Talla activada correctamente.');
        this.load();
      },
      error: () => this.toast.error('No se pudo actualizar el estado de la talla.'),
    });
  }
}
