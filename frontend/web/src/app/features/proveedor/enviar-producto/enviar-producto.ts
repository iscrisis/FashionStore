import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { PanelProveedorService } from '../shared/panel-proveedor.service';

/**
 * CU13 (panel del proveedor) -- "Enviar producto" registra solo una
 * PROPUESTA (ProductoProveedor): nombre, descripción, imagen de referencia y
 * disponibilidad. Categoría, precio, temporada, colección, tallas y colores
 * son decisiones internas de FashionStore que el Administrador completa al
 * convertir la propuesta en un Producto real (CU08) -- por eso este
 * formulario no los pide.
 */
@Component({
  selector: 'app-enviar-producto',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './enviar-producto.html',
  styleUrl: './enviar-producto.scss',
})
export class EnviarProducto {
  private readonly fb = inject(FormBuilder);
  private readonly panelService = inject(PanelProveedorService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);

  protected readonly submitting = signal(false);
  protected readonly imagenSeleccionada = signal<File | null>(null);
  protected readonly imagenPreviewUrl = signal<string | null>(null);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(150)]],
    descripcion: [''],
    disponibilidad: [true],
  });

  onImagenSeleccionada(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0] ?? null;
    if (!archivo) {
      return;
    }
    if (!['image/jpeg', 'image/jpg', 'image/png', 'image/webp'].includes(archivo.type)) {
      this.toast.error('La imagen debe ser JPG, PNG o WEBP.');
      input.value = '';
      return;
    }
    this.imagenSeleccionada.set(archivo);
    const lector = new FileReader();
    lector.onload = () => this.imagenPreviewUrl.set(lector.result as string);
    lector.readAsDataURL(archivo);
  }

  quitarImagen(): void {
    this.imagenSeleccionada.set(null);
    this.imagenPreviewUrl.set(null);
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    this.submitting.set(true);
    this.panelService
      .enviarProducto({
        nombre: value.nombre.trim(),
        descripcion: value.descripcion.trim() || null,
        disponibilidad: value.disponibilidad,
      })
      .subscribe({
        next: (producto) => {
          const archivo = this.imagenSeleccionada();
          if (!archivo) {
            this.submitting.set(false);
            this.toast.success('Producto enviado correctamente.');
            this.router.navigateByUrl('/proveedor/mis-productos');
            return;
          }
          this.panelService.establecerImagen(producto.id, archivo).subscribe({
            next: () => {
              this.submitting.set(false);
              this.toast.success('Producto enviado correctamente.');
              this.router.navigateByUrl('/proveedor/mis-productos');
            },
            error: () => {
              this.submitting.set(false);
              this.toast.error('El producto se envió, pero la imagen no se pudo guardar.');
              this.router.navigateByUrl('/proveedor/mis-productos');
            },
          });
        },
        error: () => {
          this.submitting.set(false);
          this.toast.error('No se pudo enviar el producto. Intenta nuevamente.');
        },
      });
  }
}
