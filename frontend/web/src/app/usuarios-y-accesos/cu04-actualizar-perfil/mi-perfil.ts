import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { Icon } from '../../core/ui/icon/icon';
import { ToastService } from '../../core/ui/toast/toast.service';

const TELEFONO_PATTERN = /^[0-9+\-\s()]{6,20}$/;

@Component({
  selector: 'app-mi-perfil',
  imports: [ReactiveFormsModule, RouterLink, Icon],
  templateUrl: './mi-perfil.html',
  styleUrl: './mi-perfil.scss',
})
export class MiPerfil implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly toast = inject(ToastService);

  protected readonly cargando = signal(true);
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
    correo: ['', [Validators.required, Validators.email]],
    telefono: ['', [Validators.required, Validators.pattern(TELEFONO_PATTERN)]],
  });

  ngOnInit(): void {
    // Siempre se piden los datos reales al backend (no solo lo que ya
    // guardó AuthService en localStorage) para mostrar el estado real de la
    // cuenta, incluido telefono -- que Usuario (sesión) no incluye.
    this.authService.obtenerMiPerfil().subscribe({
      next: (perfil) => {
        this.form.patchValue({
          nombre: perfil.nombre,
          correo: perfil.correo,
          telefono: perfil.telefono ?? '',
        });
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.errorMessage.set('No se pudo cargar tu perfil. Inténtalo nuevamente.');
      },
    });
  }

  submit(): void {
    if (this.submitting()) {
      return;
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const { nombre, correo, telefono } = this.form.getRawValue();
    this.submitting.set(true);
    this.errorMessage.set(null);

    this.authService.actualizarMiPerfil({ nombre, correo, telefono }).subscribe({
      next: () => {
        this.submitting.set(false);
        this.toast.success('Tus datos se actualizaron correctamente.');
      },
      error: (error: HttpErrorResponse) => {
        this.submitting.set(false);
        this.errorMessage.set(this.mensajeDeError(error));
      },
    });
  }

  private mensajeDeError(error: HttpErrorResponse): string {
    if (error.status === 0) {
      return 'No se pudo conectar con el servidor. Verifica tu conexión e inténtalo nuevamente.';
    }
    if (error.status === 409) {
      return 'Ya existe una cuenta registrada con ese correo.';
    }
    if (error.status === 422) {
      const detalle = error.error?.detail;
      if (typeof detalle === 'string') {
        return detalle;
      }
      if (Array.isArray(detalle) && typeof detalle[0]?.msg === 'string') {
        return detalle[0].msg;
      }
      return 'Revisa los datos ingresados.';
    }
    return 'Ocurrió un error al guardar tus cambios. Inténtalo nuevamente.';
  }
}
