import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SuperadminService, Empresa, Plan } from '../services/superadmin.service';
import { Icon } from '../../../core/ui/icon/icon';

interface Suscripcion {
  id: number;
  empresa_id: number;
  plan_id: number;
  fecha_inicio: string;
  fecha_vencimiento: string;
  en_prueba: boolean;
  activa: boolean;
  created_at: string;
  updated_at: string;
}

interface DetalleEmpresa {
  suscripcion: Suscripcion | null;
  empresa: Empresa;
  plan: Plan | null;
  funcionalidades_habilitadas: { [key: string]: boolean };
}

@Component({
  selector: 'app-superadmin-suscripciones',
  imports: [CommonModule, FormsModule, Icon],
  templateUrl: './suscripciones.html',
  styleUrl: './suscripciones.scss',
  standalone: true,
})
export class SuperadminSuscripciones implements OnInit {
  private readonly superadminService = inject(SuperadminService);

  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly empresas = signal<Empresa[]>([]);
  protected readonly selectedEmpresa = signal<Empresa | null>(null);
  protected readonly detalleEmpresa = signal<DetalleEmpresa | null>(null);
  protected readonly detallesMap = signal<Map<number, DetalleEmpresa>>(new Map());
  protected readonly showModalAsignar = signal(false);
  protected readonly showModalCambiar = signal(false);
  protected readonly planes = signal<Plan[]>([]);
  protected readonly submitLoading = signal(false);
  protected readonly selectedPlanId = signal<number | null>(null);

  ngOnInit(): void {
    this.cargarEmpresas();
    this.cargarPlanes();
  }

  private cargarEmpresas(): void {
    this.loading.set(true);
    this.error.set(null);
    this.superadminService.getEmpresas().subscribe({
      next: (data) => {
        this.empresas.set(data);
        this.cargarDetallesMultiples(data);
      },
      error: () => {
        this.error.set('No se pudieron cargar las empresas.');
        this.loading.set(false);
      },
    });
  }

  private cargarDetallesMultiples(empresas: Empresa[]): void {
    const detalles = new Map<number, DetalleEmpresa>();
    let cargadas = 0;
    const total = empresas.length;

    empresas.forEach((empresa) => {
      this.superadminService.getSuscripcionEmpresa(empresa.id).subscribe({
        next: (data) => {
          detalles.set(empresa.id, data);
          cargadas++;
          if (cargadas === total) {
            this.detallesMap.set(detalles);
            this.loading.set(false);
          }
        },
        error: () => {
          cargadas++;
          if (cargadas === total) {
            this.detallesMap.set(detalles);
            this.loading.set(false);
          }
        },
      });
    });
  }

  private cargarPlanes(): void {
    this.superadminService.getPlanes().subscribe({
      next: (data: any) => {
        const planesNormalizados = data.map((p: any) => ({
          ...p,
          is_active: p.es_activo !== undefined ? p.es_activo : p.is_active,
          precio: typeof p.precio === 'string' ? parseFloat(p.precio) : p.precio,
        }));
        this.planes.set(planesNormalizados);
      },
      error: () => {
        this.error.set('No se pudieron cargar los planes.');
      },
    });
  }

  seleccionarEmpresa(empresa: Empresa): void {
    this.selectedEmpresa.set(empresa);
    const detalle = this.detallesMap().get(empresa.id);
    if (detalle) {
      this.detalleEmpresa.set(detalle);
    } else {
      this.cargarDetalleEmpresa(empresa.id);
    }
  }

  private cargarDetalleEmpresa(empresaId: number): void {
    this.loading.set(true);
    this.superadminService.getSuscripcionEmpresa(empresaId).subscribe({
      next: (data: any) => {
        this.detalleEmpresa.set(data);
        const mapa = new Map(this.detallesMap());
        mapa.set(empresaId, data);
        this.detallesMap.set(mapa);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar los detalles de suscripción.');
        this.loading.set(false);
      },
    });
  }

  obtenerDetalles(empresaId: number): DetalleEmpresa | undefined {
    return this.detallesMap().get(empresaId);
  }

  abrirModalAsignar(): void {
    this.selectedPlanId.set(null);
    this.showModalAsignar.set(true);
  }

  cerrarModalAsignar(): void {
    this.showModalAsignar.set(false);
    this.selectedPlanId.set(null);
  }

  asignarPlan(): void {
    const empresa = this.selectedEmpresa();
    if (!empresa || !this.selectedPlanId()) {
      this.error.set('Seleccione un plan.');
      return;
    }

    this.submitLoading.set(true);
    const ahora = new Date();
    const vencimiento = new Date(ahora.getTime() + 365 * 24 * 60 * 60 * 1000);

    const payload = {
      empresa_id: empresa.id,
      plan_id: this.selectedPlanId(),
      fecha_inicio: ahora.toISOString(),
      fecha_vencimiento: vencimiento.toISOString(),
    };

    this.superadminService.asignarSuscripcion(payload).subscribe({
      next: () => {
        this.cargarDetalleEmpresa(empresa.id);
        this.cerrarModalAsignar();
        this.submitLoading.set(false);
      },
      error: () => {
        this.error.set('Error al asignar plan.');
        this.submitLoading.set(false);
      },
    });
  }

  abrirModalCambiar(): void {
    this.selectedPlanId.set(null);
    this.showModalCambiar.set(true);
  }

  cerrarModalCambiar(): void {
    this.showModalCambiar.set(false);
    this.selectedPlanId.set(null);
  }

  cambiarPlan(): void {
    const empresa = this.selectedEmpresa();
    if (!empresa || !this.selectedPlanId()) {
      this.error.set('Seleccione un plan.');
      return;
    }

    this.submitLoading.set(true);
    this.superadminService.cambiarSuscripcion(empresa.id, { plan_id: this.selectedPlanId() }).subscribe({
      next: () => {
        this.cargarDetalleEmpresa(empresa.id);
        this.cerrarModalCambiar();
        this.submitLoading.set(false);
      },
      error: () => {
        this.error.set('Error al cambiar plan.');
        this.submitLoading.set(false);
      },
    });
  }

  renovarSuscripcion(): void {
    const empresa = this.selectedEmpresa();
    if (!empresa) return;

    this.submitLoading.set(true);
    const vencimiento = new Date(new Date().getTime() + 365 * 24 * 60 * 60 * 1000);

    this.superadminService.renovarSuscripcion(empresa.id, { fecha_vencimiento: vencimiento.toISOString() }).subscribe({
      next: () => {
        this.cargarDetalleEmpresa(empresa.id);
        this.submitLoading.set(false);
      },
      error: () => {
        this.error.set('Error al renovar suscripción.');
        this.submitLoading.set(false);
      },
    });
  }

  cambiarEstado(activo: boolean): void {
    const empresa = this.selectedEmpresa();
    if (!empresa) return;

    this.submitLoading.set(true);
    this.superadminService.cambiarEstadoSuscripcion(empresa.id, { activa: activo }).subscribe({
      next: () => {
        this.cargarDetalleEmpresa(empresa.id);
        this.submitLoading.set(false);
      },
      error: () => {
        this.error.set('Error al cambiar estado.');
        this.submitLoading.set(false);
      },
    });
  }

  estaActiva(): boolean {
    return this.detalleEmpresa()?.suscripcion?.activa ?? false;
  }

  getNombreEstado(): string {
    return this.estaActiva() ? 'Activa' : 'Inactiva';
  }

  formatLabel(key: string): string {
    const labels: { [key: string]: string } = {
      gestion_productos: 'Gestión de productos',
      gestion_ventas: 'Gestión de ventas',
      reservas: 'Reservas',
      operacion_offline: 'Operación offline',
      reportes_convencionales: 'Reportes convencionales',
      reportes_generativos_ia: 'Reportes generativos IA',
    };
    return labels[key] || key;
  }
}
