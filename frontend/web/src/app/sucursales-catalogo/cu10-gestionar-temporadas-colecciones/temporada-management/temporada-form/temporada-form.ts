import { Component, effect, inject, input, output } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Temporada, TemporadaPayload } from '../../temporada-coleccion.model';
import { Icon } from '../../../../core/ui/icon/icon';

function rangoFechasValido(control: AbstractControl): ValidationErrors | null {
  const inicio = control.get('fecha_inicio')?.value;
  const fin = control.get('fecha_fin')?.value;
  if (!inicio || !fin) {
    return null;
  }
  return new Date(fin) < new Date(inicio) ? { rangoInvalido: true } : null;
}

@Component({
  selector: 'app-temporada-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './temporada-form.html',
  styleUrl: './temporada-form.scss',
})
export class TemporadaForm {
  readonly open = input(false);
  readonly temporada = input<Temporada | null>(null);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<TemporadaPayload>();
  readonly close = output<void>();

  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group(
    {
      nombre: ['', [Validators.required, Validators.maxLength(120)]],
      fecha_inicio: ['', [Validators.required]],
      fecha_fin: ['', [Validators.required]],
      is_active: [true],
    },
    { validators: rangoFechasValido },
  );

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const temporada = this.temporada();
      if (temporada) {
        this.form.reset({
          nombre: temporada.nombre,
          fecha_inicio: temporada.fecha_inicio,
          fecha_fin: temporada.fecha_fin,
          is_active: temporada.is_active,
        });
      } else {
        this.form.reset({ nombre: '', fecha_inicio: '', fecha_fin: '', is_active: true });
      }

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  protected get isEditMode(): boolean {
    return this.temporada() !== null;
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
      fecha_inicio: value.fecha_inicio,
      fecha_fin: value.fecha_fin,
      is_active: value.is_active,
    });
  }
}
