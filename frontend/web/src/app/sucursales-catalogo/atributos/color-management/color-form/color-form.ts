import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ColorItem, ColorPayload } from '../../models/color.model';
import { Icon } from '../../../../core/ui/icon/icon';

@Component({
  selector: 'app-color-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './color-form.html',
  styleUrl: './color-form.scss',
})
export class ColorForm {
  readonly open = input(false);
  readonly color = input<ColorItem | null>(null);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<ColorPayload>();
  readonly close = output<void>();

  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(80)]],
    is_active: [true],
  });

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const color = this.color();
      if (color) {
        this.form.reset({ nombre: color.nombre, is_active: color.is_active });
      } else {
        this.form.reset({ nombre: '', is_active: true });
      }

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  protected get isEditMode(): boolean {
    return this.color() !== null;
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
    this.save.emit({ nombre: value.nombre.trim(), is_active: value.is_active });
  }
}
