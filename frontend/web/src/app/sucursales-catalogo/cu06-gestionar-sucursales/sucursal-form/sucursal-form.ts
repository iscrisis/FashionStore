import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Icon } from '../../../core/ui/icon/icon';
import { Ciudad, SucursalAdmin } from '../sucursal-admin.model';

export interface SucursalFormValue {
  nombre: string;
  ciudad_id: number;
  direccion: string;
  telefono: string;
  is_active: boolean;
}

const TELEFONO_PATTERN = /^[0-9+\-\s()]{6,20}$/;

@Component({
  selector: 'app-sucursal-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './sucursal-form.html',
  styleUrl: './sucursal-form.scss',
})
export class SucursalForm {
  readonly open = input(false);
  readonly sucursal = input<SucursalAdmin | null>(null);
  readonly ciudades = input<Ciudad[]>([]);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<SucursalFormValue>();
  readonly close = output<void>();

  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
    ciudad_id: [null as number | null, [Validators.required]],
    direccion: ['', [Validators.required, Validators.minLength(5), Validators.maxLength(255)]],
    telefono: ['', [Validators.required, Validators.pattern(TELEFONO_PATTERN)]],
    is_active: [true],
  });

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const sucursal = this.sucursal();
      if (sucursal) {
        this.form.reset({
          nombre: sucursal.nombre,
          ciudad_id: sucursal.ciudad.id,
          direccion: sucursal.direccion,
          telefono: sucursal.telefono,
          is_active: sucursal.is_active,
        });
      } else {
        this.form.reset({ nombre: '', ciudad_id: null, direccion: '', telefono: '', is_active: true });
      }

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  protected get isEditMode(): boolean {
    return this.sucursal() !== null;
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
      ciudad_id: value.ciudad_id as number,
      direccion: value.direccion.trim(),
      telefono: value.telefono.trim(),
      is_active: value.is_active,
    });
  }
}
