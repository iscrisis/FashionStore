import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal, effect } from '@angular/core';
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
import { CommonModule } from '@angular/common';

// Mismo patrón que CU04 (actualizar-perfil, mi-perfil.ts) -- el backend
// exige exactamente esta forma para telefono (ver CU02_RegistrarCliente/
// schemas.py, _TELEFONO_PATTERN).
const TELEFONO_PATTERN = /^[0-9+\-\s()]{6,20}$/;

// Validador a nivel de formulario -- misma regla que ya exige el backend
// (ver RegistroClienteRequest._validar_confirmacion en CU02/schemas.py,
// mismo criterio que CU03 al restablecer contraseña).
function passwordsCoincidenValidator(group: AbstractControl): ValidationErrors | null {
  const password = group.get('password')?.value;
  const confirmarPassword = group.get('confirmarPassword')?.value;
  return password === confirmarPassword ? null : { passwordsNoCoinciden: true };
}

/**
 * CU02 -- Registrar cliente (público). Mismo patrón visual/estructural que
 * CU01 (login.ts) y CU03 (restablecer-contrasena.ts) -- sin guard, sin
 * sesión, "¿Ya tienes cuenta? Inicia sesión" al final.
 *
 * NO inicia sesión automáticamente: el backend (CU02/router.py) no emite
 * JWT en /auth/register a propósito -- tras un registro exitoso solo se
 * muestra una confirmación y se invita a iniciar sesión con CU01 (mismo
 * criterio que restablecer-contrasena.ts tras cambiar la contraseña).
 */
@Component({
  selector: 'app-registrar-cliente',
  imports: [ReactiveFormsModule, RouterLink, Icon, CommonModule],
  templateUrl: './registrar-cliente.html',
  styleUrl: './registrar-cliente.scss',
})
export class RegistrarCliente {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);

  protected readonly submitting = signal(false);
  protected readonly exito = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly showPassword = signal(false);
  protected readonly showConfirmarPassword = signal(false);
  protected readonly empresaSlug = signal<string | null>(null);
  protected readonly empresaNombre = signal<string | null>(null);
  protected readonly empresaCargando = signal(false);
  protected readonly empresaError = signal<string | null>(null);
  protected readonly empresas = signal<Array<{ id: number; slug: string; nombre: string }>>([]);
  protected readonly empresasListaCargando = signal(false);
  protected readonly empresasListaError = signal<string | null>(null);
  protected readonly empresaSeleccionadaSlug = signal<string | null>(null);

  protected readonly form = this.fb.nonNullable.group(
    {
      nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
      correo: ['', [Validators.required, Validators.email]],
      telefono: ['', [Validators.required, Validators.pattern(TELEFONO_PATTERN)]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmarPassword: ['', [Validators.required]],
    },
    { validators: [passwordsCoincidenValidator] },
  );

  constructor() {
    effect(() => {
      const slug = this.route.snapshot.paramMap.get('slug');
      if (slug) {
        this.empresaSlug.set(slug);
        this.cargarEmpresa(slug);
      } else {
        this.cargarEmpresas();
      }
    });
  }

  protected cargarEmpresas(): void {
    this.empresasListaCargando.set(true);
    this.empresasListaError.set(null);

    this.authService.obtenerEmpresasActivas().subscribe({
      next: (empresas) => {
        this.empresas.set(empresas);
        this.empresasListaCargando.set(false);
      },
      error: () => {
        this.empresasListaCargando.set(false);
        this.empresasListaError.set('No se pudieron cargar las empresas. Intenta nuevamente.');
      },
    });
  }

  seleccionarEmpresa(slug: string): void {
    this.empresaSeleccionadaSlug.set(slug);
    this.empresaSlug.set(slug);
    this.cargarEmpresa(slug);
  }

  private cargarEmpresa(slug: string): void {
    this.empresaCargando.set(true);
    this.empresaError.set(null);

    this.authService.obtenerEmpresa(slug).subscribe({
      next: (empresa) => {
        this.empresaCargando.set(false);
        this.empresaNombre.set(empresa.nombre);
      },
      error: () => {
        this.empresaCargando.set(false);
        this.empresaError.set('No se encontró la empresa solicitada.');
      },
    });
  }

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

    const { nombre, correo, telefono, password, confirmarPassword } = this.form.getRawValue();
    this.submitting.set(true);
    this.errorMessage.set(null);

    this.authService
      .register({
        nombre,
        correo,
        telefono,
        password,
        confirmar_password: confirmarPassword,
        empresa_slug: this.empresaSlug() || '',
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
    if (error.status === 409) {
      return typeof error.error?.detail === 'string'
        ? error.error.detail
        : 'Ya existe una cuenta registrada con ese correo.';
    }
    if (error.status === 422) {
      const detalle = error.error?.detail;
      if (Array.isArray(detalle) && typeof detalle[0]?.msg === 'string') {
        return detalle[0].msg;
      }
      return 'Revisa los datos ingresados.';
    }
    return 'Ocurrió un error al crear tu cuenta. Inténtalo nuevamente.';
  }
}
