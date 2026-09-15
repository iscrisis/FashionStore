import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Icon } from '../../../../core/ui/icon/icon';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { ProductoProveedor, ProductoProveedorPayload } from '../../shared/panel-proveedor.model';

/**
 * Ver/editar una propuesta (ProductoProveedor) ya enviada. Solo nombre y
 * descripción son editables por el proveedor -- categoría, temporada,
 * colección, precio, tallas y colores las decide el Administrador al
 * convertir la propuesta (CU08), por eso no hay campos para eso aquí.
 *
 * Si la propuesta ya fue APROBADA, muestra en solo lectura las variantes
 * reales que FashionStore definió (agrupadas por color) -- el proveedor
 * nunca puede modificarlas.
 */
@Component({
  selector: 'app-producto-editar-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './producto-editar-form.html',
  styleUrl: './producto-editar-form.scss',
})
export class ProductoEditarForm {
  readonly open = input(false);
  readonly producto = input<ProductoProveedor | null>(null);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<ProductoProveedorPayload>();
  readonly close = output<void>();

  protected readonly resolveMediaUrl = resolveMediaUrl;

  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(150)]],
    descripcion: [''],
  });

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const producto = this.producto();
      if (producto) {
        this.form.reset(
          { nombre: producto.nombre, descripcion: producto.descripcion ?? '' },
          { emitEvent: false },
        );
      } else {
        this.form.reset({ nombre: '', descripcion: '' }, { emitEvent: false });
      }

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
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
    this.save.emit({
      nombre: value.nombre.trim(),
      descripcion: value.descripcion.trim() || null,
    });
  }
}
