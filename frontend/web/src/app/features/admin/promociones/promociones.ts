import { DatePipe } from '@angular/common';
import { Component, HostListener, inject, signal } from '@angular/core';
import { ConfirmDialogService } from '../../../core/ui/confirm-dialog/confirm-dialog.service';
import { Icon } from '../../../core/ui/icon/icon';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { EstadoPromocion, PromocionDetalle, PromocionListado, PromocionPayload } from './promocion.model';
import { PromocionForm } from './promocion-form/promocion-form';
import { PromocionService } from './promocion.service';

const ETIQUETAS_ESTADO: Record<EstadoPromocion, string> = {
  PROGRAMADA: 'Programada',
  ACTIVA: 'Activa',
  FINALIZADA: 'Finalizada',
  DESACTIVADA: 'Desactivada',
};

const CLASES_ESTADO: Record<EstadoPromocion, string> = {
  PROGRAMADA: 'badge--programada',
  ACTIVA: 'badge--activa',
  FINALIZADA: 'badge--finalizada',
  DESACTIVADA: 'badge--inactive',
};

// Solo una promoción PROGRAMADA o ACTIVA admite Editar/Desactivar -- una ya
// FINALIZADA o DESACTIVADA solo se puede consultar (ver backend,
// service.py: editar() rechaza ambos estados; desactivar() no tiene sentido
// sobre algo que ya terminó o ya está apagado).
const ESTADOS_GESTIONABLES: EstadoPromocion[] = ['PROGRAMADA', 'ACTIVA'];

/**
 * CU32 -- Gestionar promociones (Administrador). Mismo patrón visual/
 * estructural que CU10 (temporada-management.ts): tabla + menú de acciones
 * por fila + drawer lateral para crear/editar/ver, nunca inventado desde
 * cero.
 *
 * "estado" SIEMPRE viene calculado del backend (PROGRAMADA/ACTIVA/
 * FINALIZADA/DESACTIVADA, ver promocion.model.ts) -- este componente nunca
 * lo deriva ni lo recalcula, solo lo traduce a texto/color.
 */
@Component({
  selector: 'app-promociones',
  imports: [DatePipe, Icon, PromocionForm],
  templateUrl: './promociones.html',
  styleUrl: './promociones.scss',
})
export class Promociones {
  private readonly service = inject(PromocionService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly promociones = signal<PromocionListado[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly drawerOpen = signal(false);
  protected readonly editingId = signal<number | null>(null);
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

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.service.list().subscribe({
      next: (promociones) => {
        this.promociones.set(promociones);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.promociones.set([]);
        this.errorMessage.set(
          'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
        );
      },
    });
  }

  openCreate(): void {
    this.editingId.set(null);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openEdit(promocion: PromocionListado): void {
    this.openMenuId.set(null);
    this.editingId.set(promocion.id);
    this.viewMode.set(false);
    this.drawerOpen.set(true);
  }

  openView(promocion: PromocionListado, event: Event): void {
    event.stopPropagation();
    this.openMenuId.set(null);
    this.editingId.set(promocion.id);
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

  esGestionable(promocion: PromocionListado): boolean {
    return ESTADOS_GESTIONABLES.includes(promocion.estado);
  }

  save(payload: PromocionPayload): void {
    const id = this.editingId();
    this.submitting.set(true);
    const request$ = id ? this.service.update(id, payload) : this.service.create(payload);

    request$.subscribe({
      next: (promocion: PromocionDetalle) => {
        this.submitting.set(false);
        this.drawerOpen.set(false);
        this.toast.success(id ? 'Promoción actualizada correctamente.' : 'Promoción creada correctamente.');
        this.load();
        void promocion;
      },
      error: (err) => {
        this.submitting.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo guardar la promoción. Inténtalo nuevamente.');
      },
    });
  }

  async desactivar(promocion: PromocionListado, event: Event): Promise<void> {
    event.stopPropagation();
    this.openMenuId.set(null);

    const confirmed = await this.confirmDialog.confirm({
      title: '¿Desactivar promoción?',
      message: `"${promocion.nombre}" dejará de aplicar el descuento de inmediato.`,
      confirmText: 'Desactivar',
      danger: true,
    });
    if (!confirmed) {
      return;
    }

    this.service.deactivate(promocion.id).subscribe({
      next: () => {
        this.toast.success('Promoción desactivada.');
        this.load();
      },
      error: () => this.toast.error('No se pudo desactivar la promoción. Inténtalo nuevamente.'),
    });
  }

  protected etiquetaEstado(estado: EstadoPromocion): string {
    return ETIQUETAS_ESTADO[estado];
  }

  protected claseEstado(estado: EstadoPromocion): string {
    return CLASES_ESTADO[estado];
  }
}
