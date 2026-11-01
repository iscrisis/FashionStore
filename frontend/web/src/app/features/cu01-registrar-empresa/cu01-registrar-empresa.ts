import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { RegistrarEmpresaService, EmpresaRegistro, Plan } from './cu01-registrar-empresa.service';

@Component({
  selector: 'app-cu01-registrar-empresa',
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './cu01-registrar-empresa.html',
  styleUrl: './cu01-registrar-empresa.scss',
  standalone: true,
})
export class RegistrarEmpresaComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(RegistrarEmpresaService);
  private readonly router = inject(Router);

  protected readonly registroForm = this.fb.group({
    // Datos de empresa
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(150)]],
    slug: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
    razon_social: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(200)]],
    correo: ['', [Validators.required, Validators.email]],
    telefono: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(30)]],
    // Datos del administrador
    nombre_admin: ['', [Validators.required, Validators.minLength(2)]],
    correo_admin: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    terminos: [false, Validators.requiredTrue],
    // Plan SaaS inicial
    plan_id: [null as number | null, Validators.required],
  });

  protected readonly enviando = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly exito = signal(false);
  protected readonly empresaCreada = signal<any>(null);
  protected readonly administradorCreado = signal<any>(null);
  protected readonly mostrarPassword = signal(false);

  // Planes
  protected readonly planes = signal<Plan[]>([]);
  protected readonly cargandoPlanes = signal(false);
  protected readonly errorPlanes = signal<string | null>(null);
  protected readonly planSeleccionado = signal<Plan | null>(null);

  ngOnInit(): void {
    this.cargarPlanes();
  }

  private cargarPlanes(): void {
    this.cargandoPlanes.set(true);
    this.errorPlanes.set(null);
    this.service.obtenerPlanesActivos().subscribe({
      next: (planes) => {
        this.planes.set(planes);
        this.cargandoPlanes.set(false);
      },
      error: () => {
        this.errorPlanes.set('No se pudieron cargar los planes disponibles. Inténtalo nuevamente.');
        this.cargandoPlanes.set(false);
      },
    });
  }

  seleccionarPlan(plan: Plan): void {
    this.planSeleccionado.set(plan);
    this.registroForm.get('plan_id')?.setValue(plan.id);
  }

  reintentar(): void {
    this.cargarPlanes();
  }

  get slugSugerido(): string {
    const nombre = this.registroForm.get('nombre')?.value || '';
    return nombre
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '-')
      .replace(/[^a-z0-9-]/g, '')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }

  onNombreChange(): void {
    const slug = this.registroForm.get('slug');
    if (!slug?.touched) {
      slug?.setValue(this.slugSugerido, { emitEvent: false });
    }
  }

  togglePasswordVisibility(): void {
    this.mostrarPassword.update((value) => !value);
  }

  onSubmit(): void {
    if (!this.registroForm.valid || this.enviando()) return;

    this.enviando.set(true);
    this.error.set(null);

    const planIdValue = this.registroForm.get('plan_id')?.value;
    const datos: EmpresaRegistro = {
      nombre: this.registroForm.get('nombre')?.value || '',
      slug: this.registroForm.get('slug')?.value || '',
      razon_social: this.registroForm.get('razon_social')?.value || '',
      correo: this.registroForm.get('correo')?.value || '',
      telefono: this.registroForm.get('telefono')?.value || '',
      nombre_admin: this.registroForm.get('nombre_admin')?.value || '',
      correo_admin: this.registroForm.get('correo_admin')?.value || '',
      password: this.registroForm.get('password')?.value || '',
      plan_id: planIdValue ? planIdValue : undefined,
    };

    this.service.registrarEmpresa(datos).subscribe({
      next: (response) => {
        this.enviando.set(false);
        this.exito.set(true);
        this.empresaCreada.set(response.empresa);
        this.administradorCreado.set(response.administrador);
      },
      error: (err) => {
        this.enviando.set(false);
        if (err.status === 409) {
          this.error.set('El nombre, identificador empresarial o correo de administrador ya existe. Verifica e intenta nuevamente.');
        } else if (err.status === 400) {
          this.error.set('Hay errores en los datos ingresados. Verifica e intenta nuevamente.');
        } else {
          this.error.set('No pudimos completar el registro. Intenta nuevamente más tarde.');
        }
      },
    });
  }

  onContinuar(): void {
    this.router.navigateByUrl('/login');
  }

  getErrorMessage(fieldName: string): string {
    const control = this.registroForm.get(fieldName);
    if (!control || !control.errors) return '';

    if (control.errors['required']) return 'Este campo es requerido.';
    if (control.errors['minlength']) return `Mínimo ${control.errors['minlength'].requiredLength} caracteres.`;
    if (control.errors['maxlength']) return `Máximo ${control.errors['maxlength'].requiredLength} caracteres.`;
    if (control.errors['email']) return 'Correo electrónico no válido.';
    if (control.errors['pattern']) return 'Formato inválido.';
    return 'Datos inválidos.';
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.registroForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }
}
