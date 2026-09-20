import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { Icon } from '../../core/ui/icon/icon';
import { RUTA_POR_ROL } from '../../core/utils/ruta-por-rol';

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
  private readonly route = inject(ActivatedRoute);

  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly showPassword = signal(false);

  // CU17 (crear reserva): si el Cliente llegó aquí porque intentó reservar
  // sin sesión, producto-detalle arma este link con ?returnUrl=/producto/id
  // (ver crear-reserva.ts) para volver exactamente a esa ficha en vez de
  // perder la intención. Se valida que sea una ruta interna (empieza con
  // "/") para no habilitar un open-redirect a un dominio externo -- no toca
  // AuthService, el interceptor ni los guards, solo decide a dónde navegar
  // después de un login exitoso.
  private readonly returnUrl = this.leerReturnUrlSeguro();

  protected readonly mensajeReserva = this.returnUrl?.includes('/producto/')
    ? 'Inicia sesión para continuar con tu reserva.'
    : null;

  private leerReturnUrlSeguro(): string | null {
    const valor = this.route.snapshot.queryParamMap.get('returnUrl');
    return valor && valor.startsWith('/') && !valor.startsWith('//') ? valor : null;
  }

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
        // RUTA_POR_ROL cubre los 5 roles reconocidos (Record exhaustivo, no
        // un if/else que pueda olvidarse de uno -- ver core/utils/ruta-por-rol.ts;
        // ese olvido era exactamente el bug: CAJERO caía en un destino '/'
        // por defecto y terminaba viéndose como un Cliente). Un rol fuera de
        // ese mapa (no debería ocurrir, el backend solo emite esos 5) nunca
        // cae a un panel por defecto: se muestra acceso no autorizado.
        const destino = RUTA_POR_ROL[response.usuario.rol];
        if (!destino) {
          this.router.navigateByUrl('/no-autorizado');
          return;
        }
        this.router.navigateByUrl(this.returnUrl ?? destino);
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
