import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule, FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import {
  SuperadminService,
  ConsultarAdministradorResponse,
  ActualizarAdministradorPayload,
} from '../services/superadmin.service';
import { Icon } from '../../../core/ui/icon/icon';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { ConfirmDialogService } from '../../../core/ui/confirm-dialog/confirm-dialog.service';

@Component({
  selector: 'app-administrador-detalle',
  imports: [CommonModule, FormsModule, ReactiveFormsModule, Icon],
  templateUrl: './administrador-detalle.html',
  styleUrl: './administrador-detalle.scss',
  standalone: true,
})
export class AdministradorDetalleComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly service = inject(SuperadminService);
  private readonly toast = inject(ToastService);
  private readonly confirmDialog = inject(ConfirmDialogService);
  private readonly fb = inject(FormBuilder);

  protected readonly loading = signal(false);
  protected readonly submitting = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly data = signal<ConsultarAdministradorResponse | null>(null);
  protected readonly editing = signal(false);

  protected form: FormGroup;

  constructor() {
    this.form = this.fb.group({
      nombre: ['', [Validators.required, Validators.minLength(2)]],
      correo: ['', [Validators.required, Validators.email]],
      is_active: [true],
    });
  }

  ngOnInit(): void {
    const empresaId = this.route.snapshot.paramMap.get('id');
    if (!empresaId) {
      this.error.set('ID de empresa no válido.');
      return;
    }

    this.cargarAdministrador(parseInt(empresaId, 10));
  }

  private cargarAdministrador(empresaId: number): void {
    this.loading.set(true);
    this.error.set(null);

    this.service.getAdministrador(empresaId).subscribe({
      next: (response) => {
        this.data.set(response);
        this.form.patchValue({
          nombre: response.administrador.nombre,
          correo: response.administrador.correo,
          is_active: response.administrador.is_active,
        });
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        if (err.status === 404) {
          this.error.set('Empresa o administrador no encontrado.');
        } else {
          this.error.set('Error al cargar los datos. Intenta nuevamente.');
        }
      },
    });
  }

  abrirEdicion(): void {
    this.editing.set(true);
  }

  cancelarEdicion(): void {
    this.editing.set(false);
    const admin = this.data()?.administrador;
    if (admin) {
      this.form.patchValue({
        nombre: admin.nombre,
        correo: admin.correo,
        is_active: admin.is_active,
      });
    }
  }

  guardarCambios(): void {
    if (this.form.invalid) {
      this.marcarTodosTocados();
      return;
    }

    const datosActuales = this.data();
    if (!datosActuales) return;

    this.submitting.set(true);

    const payload: ActualizarAdministradorPayload = this.form.getRawValue();

    this.service.updateAdministrador(datosActuales.empresa.id, payload).subscribe({
      next: (response) => {
        this.data.set(response);
        this.editing.set(false);
        this.submitting.set(false);
        this.toast.success('Administrador actualizado correctamente.');
      },
      error: (err) => {
        this.submitting.set(false);
        if (err.status === 409) {
          this.toast.error('Ya existe otro usuario con ese correo.');
        } else if (err.status === 404) {
          this.toast.error('Empresa o administrador no encontrado.');
        } else if (err.status === 400) {
          this.toast.error('Error en los datos. Intenta nuevamente.');
        } else {
          this.toast.error('No se pudo actualizar el administrador.');
        }
      },
    });
  }

  async toggleEstado(): Promise<void> {
    const admin = this.data()?.administrador;
    if (!admin) return;

    const accion = admin.is_active ? 'Desactivar' : 'Activar';
    const confirmed = await this.confirmDialog.confirm({
      title: `¿${accion} administrador?`,
      message: admin.is_active
        ? `${admin.nombre} dejará de poder iniciar sesión.`
        : `${admin.nombre} podrá volver a iniciar sesión.`,
      confirmText: accion,
      danger: admin.is_active,
    });

    if (!confirmed) return;

    const payload: ActualizarAdministradorPayload = {
      nombre: admin.nombre,
      correo: admin.correo,
      is_active: !admin.is_active,
    };

    this.service.updateAdministrador(this.data()!.empresa.id, payload).subscribe({
      next: (response) => {
        this.data.set(response);
        this.toast.success(
          !admin.is_active ? 'Administrador activado.' : 'Administrador desactivado.',
        );
      },
      error: () => {
        this.toast.error('No se pudo cambiar el estado del administrador.');
      },
    });
  }

  volver(): void {
    this.router.navigate(['/superadmin/empresas']);
  }

  private marcarTodosTocados(): void {
    Object.keys(this.form.controls).forEach((key) => {
      this.form.get(key)?.markAsTouched();
    });
  }

  getFieldError(fieldName: string): string | null {
    const control = this.form.get(fieldName);
    if (!control || !control.errors || !control.touched) {
      return null;
    }

    if (control.errors['required']) {
      return 'Este campo es obligatorio.';
    }
    if (control.errors['minlength']) {
      return `Mínimo ${control.errors['minlength'].requiredLength} caracteres.`;
    }
    if (control.errors['email']) {
      return 'Email no válido.';
    }

    return 'Campo inválido.';
  }

  isFieldInvalid(fieldName: string): boolean {
    const control = this.form.get(fieldName);
    return !!(control && control.invalid && control.touched);
  }
}
