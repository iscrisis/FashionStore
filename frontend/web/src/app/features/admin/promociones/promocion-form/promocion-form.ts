import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Icon } from '../../../../core/ui/icon/icon';
import { Producto } from '../../../../sucursales-catalogo/cu08-gestionar-productos/producto.model';
import { ProductoService } from '../../../../sucursales-catalogo/cu08-gestionar-productos/producto.service';
import { ProductoPromocion, PromocionPayload } from '../promocion.model';
import { PromocionService } from '../promocion.service';

function rangoFechasValido(control: AbstractControl): ValidationErrors | null {
  const inicio = control.get('fecha_inicio')?.value;
  const fin = control.get('fecha_fin')?.value;
  if (!inicio || !fin) {
    return null;
  }
  return new Date(fin) < new Date(inicio) ? { rangoInvalido: true } : null;
}

/**
 * CU32 -- Gestionar promociones. Drawer de crear/editar/ver, mismo patrón
 * que CU10 (temporada-form.ts): Formulario reactivo + validador de rango de
 * fechas + modo `readonly` que deshabilita todo el formulario.
 *
 * A diferencia de temporada-form, recibe solo `promocionId` (no el objeto
 * completo) -- el listado (promociones.ts) nunca trae la lista completa de
 * productos de cada promoción ("no llenar las tarjetas con la lista
 * completa de productos"), así que este drawer pide el detalle completo
 * (GET /promociones/{id}) él mismo al abrirse para editar/ver.
 *
 * El buscador de productos reutiliza ProductoService/Producto de CU08
 * (Gestionar productos) tal cual -- "mostrar productos activos del
 * catálogo", el mismo filtro `estado: 'active'` que ya usa esa pantalla,
 * sin duplicar lógica de búsqueda.
 */
@Component({
  selector: 'app-promocion-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './promocion-form.html',
  styleUrl: './promocion-form.scss',
})
export class PromocionForm {
  private readonly fb = inject(FormBuilder);
  private readonly promocionService = inject(PromocionService);
  private readonly productoService = inject(ProductoService);

  readonly open = input(false);
  readonly promocionId = input<number | null>(null);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<PromocionPayload>();
  readonly close = output<void>();

  protected readonly form = this.fb.nonNullable.group(
    {
      nombre: ['', [Validators.required, Validators.maxLength(150)]],
      porcentaje_descuento: [10, [Validators.required, Validators.min(1), Validators.max(99)]],
      fecha_inicio: ['', [Validators.required]],
      fecha_fin: ['', [Validators.required]],
    },
    { validators: rangoFechasValido },
  );

  protected readonly cargandoDetalle = signal(false);
  protected readonly productosSeleccionados = signal<Map<number, ProductoPromocion>>(new Map());
  protected readonly listaSeleccionados = computed(() => Array.from(this.productosSeleccionados().values()));

  protected readonly terminoBusqueda = signal('');
  protected readonly buscando = signal(false);
  protected readonly resultadosBusqueda = signal<Producto[]>([]);
  protected readonly intentoEnviar = signal(false);

  private searchDebounce?: ReturnType<typeof setTimeout>;

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      this.terminoBusqueda.set('');
      this.resultadosBusqueda.set([]);
      this.intentoEnviar.set(false);

      const id = this.promocionId();
      if (id === null) {
        this.form.reset({ nombre: '', porcentaje_descuento: 10, fecha_inicio: '', fecha_fin: '' });
        this.productosSeleccionados.set(new Map());
        this.aplicarModoLectura();
        return;
      }

      this.cargandoDetalle.set(true);
      this.promocionService.get(id).subscribe({
        next: (promocion) => {
          this.form.reset({
            nombre: promocion.nombre,
            porcentaje_descuento: promocion.porcentaje_descuento,
            fecha_inicio: promocion.fecha_inicio,
            fecha_fin: promocion.fecha_fin,
          });
          this.productosSeleccionados.set(new Map(promocion.productos.map((p) => [p.id, p])));
          this.cargandoDetalle.set(false);
          this.aplicarModoLectura();
        },
        error: () => {
          this.cargandoDetalle.set(false);
        },
      });
    });
  }

  private aplicarModoLectura(): void {
    if (this.readonly()) {
      this.form.disable();
    } else {
      this.form.enable();
    }
  }

  protected get isEditMode(): boolean {
    return this.promocionId() !== null;
  }

  buscarProductos(valor: string): void {
    this.terminoBusqueda.set(valor);
    clearTimeout(this.searchDebounce);
    const termino = valor.trim();
    if (!termino) {
      this.resultadosBusqueda.set([]);
      return;
    }
    this.searchDebounce = setTimeout(() => {
      this.buscando.set(true);
      this.productoService.list({ search: termino, estado: 'active' }).subscribe({
        next: (productos) => {
          this.buscando.set(false);
          this.resultadosBusqueda.set(productos);
        },
        error: () => {
          this.buscando.set(false);
          this.resultadosBusqueda.set([]);
        },
      });
    }, 350);
  }

  estaSeleccionado(productoId: number): boolean {
    return this.productosSeleccionados().has(productoId);
  }

  toggleProducto(producto: Producto): void {
    if (this.readonly()) {
      return;
    }
    this.productosSeleccionados.update((actuales) => {
      const nuevo = new Map(actuales);
      if (nuevo.has(producto.id)) {
        nuevo.delete(producto.id);
      } else {
        nuevo.set(producto.id, {
          id: producto.id,
          nombre: producto.nombre,
          imagen_principal_url: producto.imagen_principal_url,
        });
      }
      return nuevo;
    });
  }

  quitarProducto(productoId: number): void {
    if (this.readonly()) {
      return;
    }
    this.productosSeleccionados.update((actuales) => {
      const nuevo = new Map(actuales);
      nuevo.delete(productoId);
      return nuevo;
    });
  }

  submit(): void {
    if (this.readonly()) {
      return;
    }
    this.intentoEnviar.set(true);
    this.form.markAllAsTouched();
    if (this.form.invalid || this.productosSeleccionados().size === 0) {
      return;
    }
    const value = this.form.getRawValue();
    this.save.emit({
      nombre: value.nombre.trim(),
      porcentaje_descuento: value.porcentaje_descuento,
      fecha_inicio: value.fecha_inicio,
      fecha_fin: value.fecha_fin,
      producto_ids: Array.from(this.productosSeleccionados().keys()),
    });
  }
}
