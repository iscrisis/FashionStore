import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Size, SizePayload } from '../../models/size.model';
import { Icon } from '../../../../core/ui/icon/icon';

@Component({
  selector: 'app-size-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './size-form.html',
  styleUrl: './size-form.scss',
})
export class SizeForm {
  readonly open = input(false);
  readonly size = input<Size | null>(null);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<SizePayload>();
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
      const size = this.size();
      if (size) {
        this.form.reset({ nombre: size.nombre, is_active: size.is_active });
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
    return this.size() !== null;
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
