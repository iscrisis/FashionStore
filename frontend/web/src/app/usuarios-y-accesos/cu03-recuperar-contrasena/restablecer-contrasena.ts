import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { Icon } from '../../core/ui/icon/icon';

// Validador a nivel de formulario -- misma regla que ya exige el backend
// (ver ResetPasswordRequest._validar_confirmacion en CU03, mismo criterio
// que CU02 al registrarse).
function passwordsCoincidenValidator(group: AbstractControl): ValidationErrors | null {
  const password = group.get('password')?.value;
  const confirmarPassword = group.get('confirmarPassword')?.value;
  return password === confirmarPassword ? null : { passwordsNoCoinciden: true };
}

@Component({
  selector: 'app-restablecer-contrasena',
  imports: [ReactiveFormsModule, RouterLink, Icon],
  templateUrl: './restablecer-contrasena.html',
  styleUrl: './restablecer-contrasena.scss',
})
export class RestablecerContrasena {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);

  private readonly token = this.route.snapshot.queryParamMap.get('token') ?? '';

  protected readonly submitting = signal(false);
  protected readonly exito = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly showPassword = signal(false);
  protected readonly showConfirmarPassword = signal(false);
  // Sin token en la URL, el enlace es inválido de entrada -- no tiene caso
  // mostrar el formulario ni dejar que el usuario lo complete para nada.
  protected readonly enlaceInvalido = signal(this.token.length === 0);

  protected readonly form = this.fb.nonNullable.group(
    {
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmarPassword: ['', [Validators.required]],
    },
    { validators: [passwordsCoincidenValidator] },
  );

  togglePasswordVisibility(): void {
    this.showPassword.update((value) => !value);
  }

  toggleConfirmarPasswordVisibility(): void {
    this.showConfirmarPassword.update((value) => !value);
  }

  submit(): void {
    if (this.submitting()) {
      return;
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const { password, confirmarPassword } = this.form.getRawValue();
    this.submitting.set(true);
    this.errorMessage.set(null);

    this.authService
      .resetPassword({
        token: this.token,
        new_password: password,
        confirmar_password: confirmarPassword,
      })
      .subscribe({
        next: () => {
          this.submitting.set(false);
          this.exito.set(true);
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
    if (error.status === 400) {
      return typeof error.error?.detail === 'string'
        ? error.error.detail
        : 'El enlace no es válido o ya expiró. Solicita uno nuevo.';
    }
    if (error.status === 422) {
      const detalle = error.error?.detail;
      if (Array.isArray(detalle) && typeof detalle[0]?.msg === 'string') {
        return detalle[0].msg;
      }
      return 'Revisa los datos ingresados.';
    }
    return 'Ocurrió un error al actualizar tu contraseña. Inténtalo nuevamente.';
  }
}
