import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SuperadminService, Plan, PlanCrear, PlanActualizar } from '../services/superadmin.service';
import { Icon } from '../../../core/ui/icon/icon';

@Component({
  selector: 'app-superadmin-planes',
  imports: [CommonModule, FormsModule, Icon],
  templateUrl: './planes.html',
  styleUrl: './planes.scss',
  standalone: true,
})
export class SuperadminPlanes implements OnInit {
  private readonly superadminService = inject(SuperadminService);

  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly planes = signal<Plan[]>([]);
  protected readonly showModal = signal(false);
  protected readonly editingPlan = signal<Plan | null>(null);
  protected readonly formData = signal<Partial<Plan>>({});
  protected readonly submitLoading = signal(false);


  ngOnInit(): void {
    this.cargarPlanes();
  }

  private cargarPlanes(): void {
    this.loading.set(true);
    this.error.set(null);
    this.superadminService.getPlanes().subscribe({
      next: (data) => {
        // Normalizar respuesta: el backend devuelve "es_activo", convertir a "is_active"
        const planesNormalizados = data.map(p => ({
          ...p,
          is_active: p.es_activo !== undefined ? p.es_activo : p.is_active,
          precio: typeof p.precio === 'string' ? parseFloat(p.precio) : p.precio,
        }));
        this.planes.set(planesNormalizados);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar los planes.');
        this.loading.set(false);
      },
    });
  }

  abrirModalCrear(): void {
    this.editingPlan.set(null);
    this.formData.set({});
    this.showModal.set(true);
  }

  abrirModalEditar(plan: Plan): void {
    this.editingPlan.set(plan);
    this.formData.set({ ...plan });
    this.showModal.set(true);
  }

  cerrarModal(): void {
    this.showModal.set(false);
    this.editingPlan.set(null);
    this.formData.set({});
  }

  guardarPlan(): void {
    const data = this.formData();
    const plan = this.editingPlan();

    if (!data.nombre || !data.descripcion) {
      this.error.set('Los campos nombre y descripción son requeridos.');
      return;
    }

    this.submitLoading.set(true);

    if (plan) {
      // Editar
      const actualizar: PlanActualizar = {
        nombre: data.nombre,
        descripcion: data.descripcion,
        precio: data.precio,
        limite_sucursales: data.limite_sucursales,
        limite_usuarios: data.limite_usuarios,
      };

      this.superadminService.updatePlan(plan.id, actualizar).subscribe({
        next: () => {
          this.cargarPlanes();
          this.cerrarModal();
          this.submitLoading.set(false);
        },
        error: (err) => {
          this.error.set('Error al actualizar el plan.');
          this.submitLoading.set(false);
        },
      });
    } else {
      // Crear
      const nombre = data.nombre!;
      const slug = nombre
        .toLowerCase()
        .trim()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9-]/g, '');

      const crear: PlanCrear = {
        nombre,
        slug,
        descripcion: data.descripcion!,
        precio: data.precio || 0,
        limite_sucursales: data.limite_sucursales || 1,
        limite_usuarios: data.limite_usuarios || 5,
        gestion_productos: data.gestion_productos !== false,
        gestion_ventas: data.gestion_ventas !== false,
        reservas: data.reservas !== false,
        operacion_offline: data.operacion_offline !== false,
        reportes_convencionales: data.reportes_convencionales !== false,
        reportes_generativos_ia: data.reportes_generativos_ia === true,
      };

      this.superadminService.createPlan(crear).subscribe({
        next: () => {
          this.cargarPlanes();
          this.cerrarModal();
          this.submitLoading.set(false);
        },
        error: (err) => {
          this.error.set('Error al crear el plan.');
          this.submitLoading.set(false);
        },
      });
    }
  }

  toggleEstado(plan: Plan): void {
    this.superadminService
      .cambiarEstadoPlan(plan.id, { is_active: !plan.is_active })
      .subscribe({
        next: () => {
          this.cargarPlanes();
        },
        error: () => {
          this.error.set('Error al cambiar el estado del plan.');
        },
      });
  }

  eliminarPlan(plan: Plan): void {
    if (!confirm(`¿Está seguro de que desea eliminar el plan "${plan.nombre}"?`)) {
      return;
    }

    this.superadminService.deletePlan(plan.id).subscribe({
      next: () => {
        this.cargarPlanes();
      },
      error: () => {
        this.error.set('Error al eliminar el plan.');
      },
    });
  }

  reintentar(): void {
    this.cargarPlanes();
  }

  isActivo(plan: Plan): boolean {
    return plan.is_active === true;
  }
}
