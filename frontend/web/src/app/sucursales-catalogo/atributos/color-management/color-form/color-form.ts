import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ColorItem, ColorPayload } from '../../models/color.model';
import { Icon } from '../../../../core/ui/icon/icon';

const HEX_PATTERN = /^#([0-9A-Fa-f]{6})$/;

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
    name: ['', [Validators.required, Validators.maxLength(60)]],
    hexCode: ['#C1121F', [Validators.required, Validators.pattern(HEX_PATTERN)]],
    displayOrder: [1, [Validators.required, Validators.min(1)]],
    isActive: [true],
  });

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const color = this.color();
      if (color) {
        this.form.reset({
          name: color.name,
          hexCode: color.hexCode,
          displayOrder: color.displayOrder,
          isActive: color.isActive,
        });
      } else {
        this.form.reset({ name: '', hexCode: '#C1121F', displayOrder: 1, isActive: true });
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

  protected get previewColor(): string {
    const hex = this.form.controls.hexCode.value;
    return HEX_PATTERN.test(hex) ? hex : '#cccccc';
  }

  onPickerChange(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.form.controls.hexCode.setValue(value.toUpperCase());
    this.form.controls.hexCode.markAsTouched();
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
      name: value.name.trim(),
      hexCode: value.hexCode.toUpperCase(),
      displayOrder: value.displayOrder,
      isActive: value.isActive,
    });
  }
}
