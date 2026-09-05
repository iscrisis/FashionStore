import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { Icon } from '../../core/ui/icon/icon';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink, Icon],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly showPassword = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    correo: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });

  togglePasswordVisibility(): void {
    this.showPassword.update((value) => !value);
  }

  submit(): void {
    // Evita disparar múltiples peticiones por doble clic mientras ya hay una en curso.
    if (this.submitting()) {
      return;
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const { correo, password } = this.form.getRawValue();
    this.submitting.set(true);
    this.errorMessage.set(null);

    this.authService.login(correo, password).subscribe({
      next: (response) => {
        this.submitting.set(false);
        const destino = response.usuario.rol === 'ADMINISTRADOR' ? '/admin' : '/';
        this.router.navigateByUrl(destino);
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
    if (error.status === 401) {
      return 'Correo o contraseña incorrectos.';
    }
    if (error.status === 403) {
      return typeof error.error?.detail === 'string'
        ? error.error.detail
        : 'Tu cuenta está inhabilitada. Contacta al administrador.';
    }
    return 'Ocurrió un error al iniciar sesión. Inténtalo nuevamente.';
  }
}
