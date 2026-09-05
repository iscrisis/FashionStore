import { Component, HostListener, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CatalogStatusFilter } from '../models/catalog-status-filter.model';
import { ColorItem, ColorPayload } from '../models/color.model';
import { ColorService } from '../services/color.service';
import { ConfirmDialogService } from '../../../core/ui/confirm-dialog/confirm-dialog.service';
import { Icon } from '../../../core/ui/icon/icon';
import { StatusBadge } from '../../../core/ui/status-badge/status-badge';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { ColorForm } from './color-form/color-form';

@Component({
  selector: 'app-color-management',
  imports: [FormsModule, Icon, StatusBadge, ColorForm],
  templateUrl: './color-management.html',
  styleUrl: './color-management.scss',
})
export class ColorManagement {
  private readonly colorService = inject(ColorService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly colors = signal<ColorItem[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly searchTerm = signal('');
  protected readonly statusFilter = signal<CatalogStatusFilter>('all');

  protected readonly drawerOpen = signal(false);
  protected readonly editingColor = signal<ColorItem | null>(null);
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
    this.colorService
      .list({ search: this.searchTerm() || undefined, estado: this.statusFilter() })
      .subscribe({
        next: (colors) => {
          this.colors.set(colors);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.colors.set([]);
          this.errorMessage.set(
            'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
          );
        },
      });
  }

  openCreate(): void {
    this.editingColor.set(null);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openEdit(color: ColorItem): void {
    this.openMenuId.set(null);
    this.editingColor.set(color);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openView(color: ColorItem, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(null);
    this.editingColor.set(color);
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

  save(payload: ColorPayload): void {
    const editing = this.editingColor();
    this.submitting.set(true);
    const request$ = editing
      ? this.colorService.update(editing.id, payload)
      : this.colorService.create(payload);

    request$.subscribe({
      next: () => {
        this.submitting.set(false);
        this.drawerOpen.set(false);
        this.toast.success(editing ? 'Color actualizado correctamente.' : 'Color creado correctamente.');
        this.load();
      },
      error: (err) => {
        this.submitting.set(false);
        if (err.status === 409) {
          this.toast.error('Ya existe un color con ese nombre.');
        } else {
          this.toast.error('No se pudo guardar el color. Intenta nuevamente.');
        }
      },
    });
  }

  async toggleStatus(color: ColorItem, event: Event): Promise<void> {
    event.stopPropagation();
    this.openMenuId.set(null);

    if (color.is_active) {
      const confirmed = await this.confirmDialog.confirm({
        title: '¿Desactivar color?',
        message: 'El color dejará de estar disponible para nuevas prendas.',
        confirmText: 'Desactivar',
        danger: true,
      });
      if (!confirmed) {
        return;
      }
    }

    this.colorService.setActive(color.id, !color.is_active).subscribe({
      next: () => {
        this.toast.success(color.is_active ? 'Color desactivado.' : 'Color activado correctamente.');
        this.load();
      },
      error: () => this.toast.error('No se pudo actualizar el estado del color.'),
    });
  }
}
