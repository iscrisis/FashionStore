import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ConfirmDialogService } from '../../../core/ui/confirm-dialog/confirm-dialog.service';
import { Icon } from '../../../core/ui/icon/icon';
import { StatusBadge } from '../../../core/ui/status-badge/status-badge';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { EstadoPropuesta, PropuestaProveedor } from '../producto.model';
import { ProductoService } from '../producto.service';
import { ProductoForm, ProductoFormValue } from '../producto-form/producto-form';

/**
 * CU08 -- "Propuestas de proveedores": el Administrador revisa cada
 * ProductoProveedor (CU13) y decide Aprobar (reutiliza ProductoForm para
 * convertirla en un Producto real) o Rechazar (PATCH /propuestas/{id}/rechazar,
 * ver CU08 service.rechazar_propuesta) -- ningún flujo nuevo, solo esta
 * pantalla de revisión sobre lo que ya existe.
 */
@Component({
  selector: 'app-propuestas-proveedor',
  imports: [FormsModule, Icon, StatusBadge, ProductoForm],
  templateUrl: './propuestas-proveedor.html',
  styleUrl: './propuestas-proveedor.scss',
})
export class PropuestasProveedor {
  private readonly productoService = inject(ProductoService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly propuestas = signal<PropuestaProveedor[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly filtroEstado = signal<EstadoPropuesta>('PENDIENTE');

  protected readonly revisando = signal<PropuestaProveedor | null>(null);
  protected readonly aprobando = signal<PropuestaProveedor | null>(null);
  protected readonly rechazandoId = signal<number | null>(null);
  protected readonly submittingAprobar = signal(false);

  constructor() {
    this.load();
  }

  onFiltroChange(value: string): void {
    this.filtroEstado.set(value as EstadoPropuesta);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.productoService.listPropuestas(this.filtroEstado()).subscribe({
      next: (propuestas) => {
        this.propuestas.set(propuestas);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.propuestas.set([]);
        this.errorMessage.set(
          'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
        );
      },
    });
  }

  abrirRevision(propuesta: PropuestaProveedor): void {
    this.revisando.set(propuesta);
  }

  cerrarRevision(): void {
    this.revisando.set(null);
  }

  iniciarAprobacion(): void {
    const propuesta = this.revisando();
    if (!propuesta) {
      return;
    }
    this.aprobando.set(propuesta);
    this.revisando.set(null);
  }

  cerrarAprobacion(): void {
    this.aprobando.set(null);
  }

  guardarAprobacion(payload: ProductoFormValue): void {
    this.submittingAprobar.set(true);
    this.productoService.create(payload).subscribe({
      next: () => {
        this.submittingAprobar.set(false);
        this.aprobando.set(null);
        this.toast.success('Propuesta aprobada: el producto ya está creado.');
        this.load();
      },
      error: (err) => {
        this.submittingAprobar.set(false);
        if (err.status === 409) {
          this.toast.error('Esa propuesta ya fue aprobada o rechazada.');
        } else if (err.status === 422) {
          this.toast.error('Revisa los datos ingresados: alguna referencia seleccionada no es válida.');
        } else {
          this.toast.error('No se pudo aprobar la propuesta. Intenta nuevamente.');
        }
      },
    });
  }

  async rechazar(propuesta: PropuestaProveedor): Promise<void> {
    const confirmado = await this.confirmDialog.confirm({
      title: '¿Rechazar propuesta?',
      message: `"${propuesta.nombre}" de ${propuesta.proveedor.razon_social} quedará marcada como rechazada. El proveedor seguirá viéndola en su historial, pero no se convertirá en un producto.`,
      confirmText: 'Rechazar',
      danger: true,
    });
    if (!confirmado) {
      return;
    }

    this.rechazandoId.set(propuesta.id);
    this.productoService.rechazarPropuesta(propuesta.id).subscribe({
      next: () => {
        this.rechazandoId.set(null);
        this.revisando.set(null);
        this.toast.success('Propuesta rechazada.');
        this.load();
      },
      error: () => {
        this.rechazandoId.set(null);
        this.toast.error('No se pudo rechazar la propuesta. Intenta nuevamente.');
      },
    });
  }
}
