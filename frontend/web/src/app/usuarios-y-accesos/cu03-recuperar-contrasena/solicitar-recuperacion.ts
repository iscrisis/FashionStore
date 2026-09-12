import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { Icon } from '../../core/ui/icon/icon';

const MENSAJE_GENERICO =
  'Si existe una cuenta asociada a ese correo, recibirás un enlace para restablecer tu contraseña.';

@Component({
  selector: 'app-solicitar-recuperacion',
  imports: [ReactiveFormsModule, RouterLink, Icon],
  templateUrl: './solicitar-recuperacion.html',
  styleUrl: './solicitar-recuperacion.scss',
})
export class SolicitarRecuperacion {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);

  protected readonly submitting = signal(false);
  protected readonly enviado = signal(false);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly form = this.fb.nonNullable.group({
    correo: ['', [Validators.required, Validators.email]],
  });

  submit(): void {
    if (this.submitting()) {
      return;
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const { correo } = this.form.getRawValue();
    this.submitting.set(true);
    this.errorMessage.set(null);

    this.authService.forgotPassword(correo).subscribe({
      // El backend responde el mismo mensaje genérico exista o no la cuenta
      // (ver CU03/router.py) -- este formulario nunca distingue el caso.
      next: () => {
        this.submitting.set(false);
        this.enviado.set(true);
      },
      error: (error: HttpErrorResponse) => {
        this.submitting.set(false);
        // Un error de red/servidor sí se informa (distinto de "correo no
        // encontrado", que el backend nunca revela); en ese caso tampoco se
        // marca enviado() para permitir reintentar.
        this.errorMessage.set(
          error.status === 0
            ? 'No se pudo conectar con el servidor. Verifica tu conexión e inténtalo nuevamente.'
            : 'Ocurrió un error al procesar tu solicitud. Inténtalo nuevamente.',
        );
      },
    });
  }

  protected readonly mensajeGenerico = MENSAJE_GENERICO;
}
