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
    code: ['', [Validators.required, Validators.maxLength(10)]],
    name: ['', [Validators.required, Validators.maxLength(60)]],
    description: [''],
    displayOrder: [1, [Validators.required, Validators.min(1)]],
    isActive: [true],
  });

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const size = this.size();
      if (size) {
        this.form.reset({
          code: size.code,
          name: size.name,
          description: size.description ?? '',
          displayOrder: size.displayOrder,
          isActive: size.isActive,
        });
      } else {
        this.form.reset({ code: '', name: '', description: '', displayOrder: 1, isActive: true });
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
    this.save.emit({
      code: value.code.trim().toUpperCase(),
      name: value.name.trim(),
      description: value.description.trim() || null,
      displayOrder: value.displayOrder,
      isActive: value.isActive,
    });
  }
}
