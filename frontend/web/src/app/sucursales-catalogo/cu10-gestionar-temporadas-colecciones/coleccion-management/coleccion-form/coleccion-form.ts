import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Coleccion, ColeccionPayload, Temporada } from '../../temporada-coleccion.model';
import { Icon } from '../../../../core/ui/icon/icon';

@Component({
  selector: 'app-coleccion-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './coleccion-form.html',
  styleUrl: './coleccion-form.scss',
})
export class ColeccionForm {
  readonly open = input(false);
  readonly coleccion = input<Coleccion | null>(null);
  readonly temporadas = input<Temporada[]>([]);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<ColeccionPayload>();
  readonly close = output<void>();

  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(120)]],
    temporada_id: [null as number | null, [Validators.required]],
    descripcion: [''],
    is_active: [true],
  });

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const coleccion = this.coleccion();
      if (coleccion) {
        this.form.reset({
          nombre: coleccion.nombre,
          temporada_id: coleccion.temporada.id,
          descripcion: coleccion.descripcion ?? '',
          is_active: coleccion.is_active,
        });
      } else {
        this.form.reset({ nombre: '', temporada_id: null, descripcion: '', is_active: true });
      }

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  protected get isEditMode(): boolean {
    return this.coleccion() !== null;
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
      temporada_id: value.temporada_id as number,
      descripcion: value.descripcion.trim() || null,
      is_active: value.is_active,
    });
  }
}
