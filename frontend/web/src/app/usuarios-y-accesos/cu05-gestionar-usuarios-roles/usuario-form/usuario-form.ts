import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Icon } from '../../../core/ui/icon/icon';
import { RolAsignableCU05, RolDisponible, UsuarioAdmin } from '../usuario-admin.model';

export interface UsuarioFormValue {
  nombre: string;
  correo: string;
  password?: string;
  rol: RolAsignableCU05;
  is_active: boolean;
}

@Component({
  selector: 'app-usuario-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './usuario-form.html',
  styleUrl: './usuario-form.scss',
})
export class UsuarioForm {
  readonly open = input(false);
  readonly usuario = input<UsuarioAdmin | null>(null);
  readonly roles = input<RolDisponible[]>([]);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<UsuarioFormValue>();
  readonly close = output<void>();

  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(120)]],
    correo: ['', [Validators.required, Validators.email]],
    password: [''],
    rol: ['' as RolAsignableCU05, [Validators.required]],
    is_active: [true],
  });

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const usuario = this.usuario();
      if (usuario) {
        this.form.reset({
          nombre: usuario.nombre,
          correo: usuario.correo,
          password: '',
          rol: usuario.rol as RolAsignableCU05,
          is_active: usuario.is_active,
        });
        this.form.controls.password.clearValidators();
      } else {
        this.form.reset({ nombre: '', correo: '', password: '', rol: '' as RolAsignableCU05, is_active: true });
        this.form.controls.password.setValidators([Validators.required, Validators.minLength(8)]);
      }
      this.form.controls.password.updateValueAndValidity();

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  protected get isEditMode(): boolean {
    return this.usuario() !== null;
  }

  submit(): void {
    if (this.readonly()) {
      return;
    }
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    this.save.emit({
      nombre: value.nombre.trim(),
      correo: value.correo.trim().toLowerCase(),
      password: value.password ? value.password : undefined,
      rol: value.rol,
      is_active: value.is_active,
    });
  }
}
