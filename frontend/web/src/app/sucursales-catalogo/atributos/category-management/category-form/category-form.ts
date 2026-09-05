import { Component, effect, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { Category, CategoryPayload } from '../../models/category.model';
import { CategoryService } from '../../services/category.service';
import { Icon } from '../../../../core/ui/icon/icon';

const FORMATOS_IMAGEN_PERMITIDOS = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
const TAMANO_MAXIMO_IMAGEN_BYTES = 5 * 1024 * 1024;

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
  private readonly categoryService = inject(CategoryService);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(80)]],
    is_active: [true],
  });

  protected readonly imagenUrl = signal<string | null>(null);
  protected readonly subiendoImagen = signal(false);
  protected readonly imagenError = signal<string | null>(null);
  protected readonly resolveMediaUrl = resolveMediaUrl;

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const category = this.category();
      this.imagenError.set(null);
      if (category) {
        this.form.reset({ nombre: category.nombre, is_active: category.is_active });
        this.imagenUrl.set(category.imagen_url);
      } else {
        this.form.reset({ nombre: '', is_active: true });
        this.imagenUrl.set(null);
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

  onImagenSeleccionada(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0];
    input.value = '';
    const category = this.category();
    if (!archivo || !category) {
      return;
    }
    if (!FORMATOS_IMAGEN_PERMITIDOS.includes(archivo.type)) {
      this.imagenError.set('La imagen debe ser un archivo JPG, JPEG, PNG o WEBP.');
      return;
    }
    if (archivo.size > TAMANO_MAXIMO_IMAGEN_BYTES) {
      this.imagenError.set('La imagen no puede superar los 5 MB.');
      return;
    }

    this.imagenError.set(null);
    this.subiendoImagen.set(true);
    this.categoryService.setImagen(category.id, archivo).subscribe({
      next: (actualizada) => {
        this.subiendoImagen.set(false);
        this.imagenUrl.set(actualizada.imagen_url);
      },
      error: () => {
        this.subiendoImagen.set(false);
        this.imagenError.set('No se pudo cargar la imagen. Intenta nuevamente.');
      },
    });
  }

  quitarImagen(): void {
    const category = this.category();
    if (!category) {
      return;
    }
    this.categoryService.removeImagen(category.id).subscribe({
      next: () => this.imagenUrl.set(null),
      error: () => this.imagenError.set('No se pudo quitar la imagen. Intenta nuevamente.'),
    });
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
