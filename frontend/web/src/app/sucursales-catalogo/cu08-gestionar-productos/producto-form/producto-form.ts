import { Component, effect, inject, input, output, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormsModule,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { Icon } from '../../../core/ui/icon/icon';
import { Category } from '../../atributos/models/category.model';
import { ColorItem } from '../../atributos/models/color.model';
import { Size } from '../../atributos/models/size.model';
import { CategoryService } from '../../atributos/services/category.service';
import { ColorService } from '../../atributos/services/color.service';
import { SizeService } from '../../atributos/services/size.service';
import { ColeccionAdminService } from '../../cu10-gestionar-temporadas-colecciones/coleccion-admin.service';
import { TemporadaAdminService } from '../../cu10-gestionar-temporadas-colecciones/temporada-admin.service';
import { Coleccion, Temporada } from '../../cu10-gestionar-temporadas-colecciones/temporada-coleccion.model';
import { Proveedor } from '../../gestion-proveedores/proveedor.model';
import { ProveedorService } from '../../gestion-proveedores/proveedor.service';
import { Producto, ProductoImagen, ProductoPayload, PropuestaProveedor } from '../producto.model';
import { ProductoService } from '../producto.service';

export type ProductoFormValue = ProductoPayload;

const FORMATOS_IMAGEN_PERMITIDOS = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
const TAMANO_MAXIMO_IMAGEN_BYTES = 5 * 1024 * 1024;

function precioPositivoValidator(control: AbstractControl): ValidationErrors | null {
  const valor = parseFloat(control.value);
  return !isNaN(valor) && valor > 0 ? null : { precioInvalido: true };
}

@Component({
  selector: 'app-producto-form',
  imports: [ReactiveFormsModule, FormsModule, Icon],
  templateUrl: './producto-form.html',
  styleUrl: './producto-form.scss',
})
export class ProductoForm {
  readonly open = input(false);
  readonly producto = input<Producto | null>(null);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<ProductoFormValue>();
  readonly close = output<void>();

  private readonly fb = inject(FormBuilder);
  private readonly categoryService = inject(CategoryService);
  private readonly sizeService = inject(SizeService);
  private readonly colorService = inject(ColorService);
  private readonly temporadaService = inject(TemporadaAdminService);
  private readonly coleccionService = inject(ColeccionAdminService);
  private readonly proveedorService = inject(ProveedorService);
  private readonly productoService = inject(ProductoService);

  protected readonly categorias = signal<Category[]>([]);
  protected readonly tallas = signal<Size[]>([]);
  protected readonly colores = signal<ColorItem[]>([]);
  protected readonly temporadas = signal<Temporada[]>([]);
  protected readonly colecciones = signal<Coleccion[]>([]);
  protected readonly proveedores = signal<Proveedor[]>([]);
  protected readonly propuestas = signal<PropuestaProveedor[]>([]);

  protected readonly imagenPrincipalUrl = signal<string | null>(null);
  protected readonly imagenesAdicionales = signal<ProductoImagen[]>([]);
  protected readonly subiendoPrincipal = signal(false);
  protected readonly subiendoAdicional = signal(false);
  protected readonly imagenError = signal<string | null>(null);
  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly form = this.fb.group({
    propuesta_id: this.fb.control<number | null>(null),
    nombre: this.fb.nonNullable.control('', [
      Validators.required,
      Validators.minLength(2),
      Validators.maxLength(150),
    ]),
    descripcion: this.fb.nonNullable.control(''),
    proveedor_id: this.fb.control<number | null>(null, Validators.required),
    categoria_id: this.fb.control<number | null>(null, Validators.required),
    temporada_id: this.fb.control<number | null>(null, Validators.required),
    coleccion_id: this.fb.control<number | null>(null, Validators.required),
    precio_venta: this.fb.nonNullable.control('', [
      Validators.required,
      Validators.pattern(/^\d+(\.\d{1,2})?$/),
      precioPositivoValidator,
    ]),
    talla_ids: this.fb.nonNullable.control<number[]>([]),
    color_ids: this.fb.nonNullable.control<number[]>([]),
    is_active: this.fb.nonNullable.control(true),
  });

  constructor() {
    this.categoryService.list({ estado: 'active' }).subscribe((valores) => this.categorias.set(valores));
    this.sizeService.list({ estado: 'active' }).subscribe((valores) => this.tallas.set(valores));
    this.colorService.list({ estado: 'active' }).subscribe((valores) => this.colores.set(valores));
    this.temporadaService.list({ estado: 'active' }).subscribe((valores) => this.temporadas.set(valores));
    this.proveedorService.list({ estado: 'active' }).subscribe((valores) => this.proveedores.set(valores));

    effect(() => {
      if (!this.open()) {
        return;
      }
      const producto = this.producto();
      this.imagenError.set(null);

      if (producto) {
        this.propuestas.set([]);
        this.colecciones.set([]);
        this.imagenPrincipalUrl.set(producto.imagen_principal_url);
        this.imagenesAdicionales.set(producto.imagenes);
        this.coleccionService
          .list({ temporada_id: producto.temporada.id })
          .subscribe((valores) => this.colecciones.set(valores));
        this.form.reset({
          propuesta_id: null,
          nombre: producto.nombre,
          descripcion: producto.descripcion ?? '',
          proveedor_id: producto.proveedor.id,
          categoria_id: producto.categoria.id,
          temporada_id: producto.temporada.id,
          coleccion_id: producto.coleccion.id,
          precio_venta: producto.precio_venta,
          talla_ids: producto.tallas.map((talla) => talla.id),
          color_ids: producto.colores.map((color) => color.id),
          is_active: producto.is_active,
        });
      } else {
        this.colecciones.set([]);
        this.imagenPrincipalUrl.set(null);
        this.imagenesAdicionales.set([]);
        this.form.reset({
          propuesta_id: null,
          nombre: '',
          descripcion: '',
          proveedor_id: null,
          categoria_id: null,
          temporada_id: null,
          coleccion_id: null,
          precio_venta: '',
          talla_ids: [],
          color_ids: [],
          is_active: true,
        });
        this.productoService.listPropuestas().subscribe((valores) => this.propuestas.set(valores));
      }

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  protected get isEditMode(): boolean {
    return this.producto() !== null;
  }

  onTemporadaChange(value: string): void {
    const temporadaId = value ? Number(value) : null;
    this.form.controls.temporada_id.setValue(temporadaId);
    this.form.controls.coleccion_id.setValue(null);
    this.colecciones.set([]);
    if (temporadaId) {
      this.coleccionService
        .list({ temporada_id: temporadaId, estado: 'active' })
        .subscribe((valores) => this.colecciones.set(valores));
    }
  }

  onPropuestaChange(value: string): void {
    const propuestaId = value ? Number(value) : null;
    this.form.controls.propuesta_id.setValue(propuestaId);
    if (!propuestaId) {
      return;
    }
    const propuesta = this.propuestas().find((item) => item.id === propuestaId);
    if (!propuesta) {
      return;
    }
    this.form.patchValue({
      nombre: propuesta.nombre,
      descripcion: propuesta.descripcion ?? '',
      proveedor_id: propuesta.proveedor.id,
      temporada_id: propuesta.temporada.id,
    });
    this.coleccionService
      .list({ temporada_id: propuesta.temporada.id, estado: 'active' })
      .subscribe((valores) => {
        this.colecciones.set(valores);
        this.form.controls.coleccion_id.setValue(propuesta.coleccion.id);
      });
  }

  toggleTalla(id: number): void {
    if (this.readonly()) {
      return;
    }
    const actuales = this.form.controls.talla_ids.value;
    this.form.controls.talla_ids.setValue(
      actuales.includes(id) ? actuales.filter((valor) => valor !== id) : [...actuales, id],
    );
  }

  toggleColor(id: number): void {
    if (this.readonly()) {
      return;
    }
    const actuales = this.form.controls.color_ids.value;
    this.form.controls.color_ids.setValue(
      actuales.includes(id) ? actuales.filter((valor) => valor !== id) : [...actuales, id],
    );
  }

  private validarArchivoImagen(archivo: File): boolean {
    if (!FORMATOS_IMAGEN_PERMITIDOS.includes(archivo.type)) {
      this.imagenError.set('La imagen debe ser un archivo JPG, JPEG, PNG o WEBP.');
      return false;
    }
    if (archivo.size > TAMANO_MAXIMO_IMAGEN_BYTES) {
      this.imagenError.set('La imagen no puede superar los 5 MB.');
      return false;
    }
    this.imagenError.set(null);
    return true;
  }

  onPrincipalFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0];
    input.value = '';
    const producto = this.producto();
    if (!archivo || !producto || !this.validarArchivoImagen(archivo)) {
      return;
    }

    this.subiendoPrincipal.set(true);
    this.productoService.setImagenPrincipal(producto.id, archivo).subscribe({
      next: (actualizado) => {
        this.subiendoPrincipal.set(false);
        this.imagenPrincipalUrl.set(actualizado.imagen_principal_url);
      },
      error: () => {
        this.subiendoPrincipal.set(false);
        this.imagenError.set('No se pudo cargar la imagen principal. Intenta nuevamente.');
      },
    });
  }

  onImagenAdicionalSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0];
    input.value = '';
    const producto = this.producto();
    if (!archivo || !producto || !this.validarArchivoImagen(archivo)) {
      return;
    }

    this.subiendoAdicional.set(true);
    this.productoService.addImagen(producto.id, archivo).subscribe({
      next: (actualizado) => {
        this.subiendoAdicional.set(false);
        this.imagenesAdicionales.set(actualizado.imagenes);
      },
      error: () => {
        this.subiendoAdicional.set(false);
        this.imagenError.set('No se pudo cargar la imagen. Intenta nuevamente.');
      },
    });
  }

  removeImagen(imagenId: number): void {
    const producto = this.producto();
    if (!producto) {
      return;
    }
    this.productoService.removeImagen(producto.id, imagenId).subscribe({
      next: (actualizado) => this.imagenesAdicionales.set(actualizado.imagenes),
      error: () => this.imagenError.set('No se pudo eliminar la imagen. Intenta nuevamente.'),
    });
  }

  submit(): void {
    if (this.readonly()) {
      return;
    }

    const sinTallas = this.form.controls.talla_ids.value.length === 0;
    const sinColores = this.form.controls.color_ids.value.length === 0;

    if (this.form.invalid || sinTallas || sinColores) {
      this.form.markAllAsTouched();
      return;
    }

    const value = this.form.getRawValue();
    const producto = this.producto();
    this.save.emit({
      nombre: value.nombre.trim(),
      descripcion: value.descripcion.trim() || null,
      proveedor_id: value.proveedor_id!,
      producto_proveedor_id: producto ? producto.producto_proveedor_id : value.propuesta_id,
      categoria_id: value.categoria_id!,
      temporada_id: value.temporada_id!,
      coleccion_id: value.coleccion_id!,
      precio_venta: value.precio_venta,
      talla_ids: value.talla_ids,
      color_ids: value.color_ids,
      is_active: value.is_active,
    });
  }
}
