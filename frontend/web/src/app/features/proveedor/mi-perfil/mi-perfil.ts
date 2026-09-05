import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { StatusBadge } from '../../../core/ui/status-badge/status-badge';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { MiProveedor } from '../shared/panel-proveedor.model';
import { PanelProveedorService } from '../shared/panel-proveedor.service';

const TELEFONO_PATTERN = /^[0-9+\-\s()]{6,20}$/;

@Component({
  selector: 'app-mi-perfil',
  imports: [ReactiveFormsModule, StatusBadge],
  templateUrl: './mi-perfil.html',
  styleUrl: './mi-perfil.scss',
})
export class MiPerfil {
  private readonly fb = inject(FormBuilder);
  private readonly panelService = inject(PanelProveedorService);
  private readonly toast = inject(ToastService);

  protected readonly perfil = signal<MiProveedor | null>(null);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly submitting = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    razon_social: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(150)]],
    nombre_contacto: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
    correo: ['', [Validators.required, Validators.email]],
    telefono: ['', [Validators.required, Validators.pattern(TELEFONO_PATTERN)]],
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.panelService.miPerfil().subscribe({
      next: (perfil) => {
        this.perfil.set(perfil);
        this.form.reset({
          razon_social: perfil.razon_social,
          nombre_contacto: perfil.nombre_contacto,
          correo: perfil.correo,
          telefono: perfil.telefono,
        });
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.errorMessage.set(
          'No se pudo conectar con el servidor. Verifica que la API esté disponible e inténtalo nuevamente.',
        );
      },
    });
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    this.submitting.set(true);
    this.panelService
      .actualizarMiPerfil({
        razon_social: value.razon_social.trim(),
        nombre_contacto: value.nombre_contacto.trim(),
        correo: value.correo.trim().toLowerCase(),
        telefono: value.telefono.trim(),
      })
      .subscribe({
        next: (perfil) => {
          this.submitting.set(false);
          this.perfil.set(perfil);
          this.toast.success('Perfil actualizado correctamente.');
        },
        error: (err) => {
          this.submitting.set(false);
          if (err.status === 409) {
            this.toast.error('Ya existe un proveedor con esa razón social.');
          } else {
            this.toast.error('No se pudo guardar tu perfil. Intenta nuevamente.');
          }
        },
      });
  }
}
