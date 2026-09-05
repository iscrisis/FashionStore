import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Proveedor } from '../proveedor.model';
import { Icon } from '../../../core/ui/icon/icon';

export interface ProveedorFormValue {
  razon_social: string;
  nombre_contacto: string;
  correo: string;
  telefono: string;
  is_active: boolean;
}

const TELEFONO_PATTERN = /^[0-9+\-\s()]{6,20}$/;

@Component({
  selector: 'app-proveedor-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './proveedor-form.html',
  styleUrl: './proveedor-form.scss',
})
export class ProveedorForm {
  readonly open = input(false);
  readonly proveedor = input<Proveedor | null>(null);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<ProveedorFormValue>();
  readonly close = output<void>();

  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group({
    razon_social: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(150)]],
    nombre_contacto: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
    correo: ['', [Validators.required, Validators.email]],
    telefono: ['', [Validators.required, Validators.pattern(TELEFONO_PATTERN)]],
    is_active: [true],
  });

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const proveedor = this.proveedor();
      if (proveedor) {
        this.form.reset({
          razon_social: proveedor.razon_social,
          nombre_contacto: proveedor.nombre_contacto,
          correo: proveedor.correo,
          telefono: proveedor.telefono,
          is_active: proveedor.is_active,
        });
      } else {
        this.form.reset({
          razon_social: '',
          nombre_contacto: '',
          correo: '',
          telefono: '',
          is_active: true,
        });
      }

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  protected get isEditMode(): boolean {
    return this.proveedor() !== null;
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
      razon_social: value.razon_social.trim(),
      nombre_contacto: value.nombre_contacto.trim(),
      correo: value.correo.trim().toLowerCase(),
      telefono: value.telefono.trim(),
      is_active: value.is_active,
    });
  }
}
