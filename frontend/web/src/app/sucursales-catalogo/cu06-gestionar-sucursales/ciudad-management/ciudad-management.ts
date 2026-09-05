import { Component, effect, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { Icon } from '../../../core/ui/icon/icon';
import { StatusBadge } from '../../../core/ui/status-badge/status-badge';
import { Ciudad } from '../sucursal-admin.model';
import { SucursalAdminService } from '../sucursal-admin.service';

@Component({
  selector: 'app-ciudad-management',
  imports: [ReactiveFormsModule, Icon, StatusBadge],
  templateUrl: './ciudad-management.html',
  styleUrl: './ciudad-management.scss',
})
export class CiudadManagement {
  readonly open = input(false);

  readonly close = output<void>();
  readonly changed = output<void>();

  private readonly fb = inject(FormBuilder);
  private readonly ciudadService = inject(SucursalAdminService);
  private readonly toast = inject(ToastService);

  protected readonly ciudades = signal<Ciudad[]>([]);
  protected readonly loading = signal(true);
  protected readonly submitting = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
    departamento: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
    is_active: [true],
  });

  constructor() {
    effect(() => {
      if (this.open()) {
        this.load();
      }
    });
  }

  private load(): void {
    this.loading.set(true);
    this.ciudadService.ciudades().subscribe({
      next: (ciudades) => {
        this.ciudades.set(ciudades);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  submitCrear(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    this.submitting.set(true);
    this.ciudadService
      .createCiudad({
        nombre: value.nombre.trim(),
        departamento: value.departamento.trim(),
        is_active: value.is_active,
      })
      .subscribe({
        next: () => {
          this.submitting.set(false);
          this.form.reset({ nombre: '', departamento: '', is_active: true });
          this.toast.success('Ciudad creada correctamente.');
          this.load();
          this.changed.emit();
        },
        error: (err) => {
          this.submitting.set(false);
          if (err.status === 409) {
            this.toast.error('Ya existe una ciudad con ese nombre.');
          } else {
            this.toast.error('No se pudo crear la ciudad. Intenta nuevamente.');
          }
        },
      });
  }

  toggleStatus(ciudad: Ciudad): void {
    this.ciudadService.setCiudadActive(ciudad.id, !ciudad.is_active).subscribe({
      next: () => {
        this.toast.success(ciudad.is_active ? 'Ciudad desactivada.' : 'Ciudad activada correctamente.');
        this.load();
        this.changed.emit();
      },
      error: () => this.toast.error('No se pudo actualizar el estado de la ciudad.'),
    });
  }
}
