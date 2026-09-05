import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Category, CategoryPayload } from '../../models/category.model';
import { Icon } from '../../../../core/ui/icon/icon';

@Component({
  selector: 'app-category-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './category-form.html',
  styleUrl: './category-form.scss',
})
export class CategoryForm {
  readonly open = input(false);
  readonly category = input<Category | null>(null);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<CategoryPayload>();
  readonly close = output<void>();

  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(80)]],
    description: [''],
    imageUrl: [''],
    displayOrder: [1, [Validators.required, Validators.min(1)]],
    isActive: [true],
  });

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const category = this.category();
      if (category) {
        this.form.reset({
          name: category.name,
          description: category.description ?? '',
          imageUrl: category.imageUrl ?? '',
          displayOrder: category.displayOrder,
          isActive: category.isActive,
        });
      } else {
        this.form.reset({ name: '', description: '', imageUrl: '', displayOrder: 1, isActive: true });
      }

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  protected get isEditMode(): boolean {
    return this.category() !== null;
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
      description: value.description.trim() || null,
      imageUrl: value.imageUrl.trim() || null,
      displayOrder: value.displayOrder,
      isActive: value.isActive,
    });
  }
}
