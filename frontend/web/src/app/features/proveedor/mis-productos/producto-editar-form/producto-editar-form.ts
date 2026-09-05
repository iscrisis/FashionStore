import { Component, effect, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Icon } from '../../../../core/ui/icon/icon';
import {
  ColeccionResumen,
  ProductoProveedor,
  ProductoProveedorPayload,
  TemporadaResumen,
} from '../../shared/panel-proveedor.model';
import { PanelProveedorService } from '../../shared/panel-proveedor.service';

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

  private readonly fb = inject(FormBuilder);
  private readonly panelService = inject(PanelProveedorService);

  protected readonly temporadas = signal<TemporadaResumen[]>([]);
  protected readonly colecciones = signal<ColeccionResumen[]>([]);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(150)]],
    descripcion: [''],
    temporada_id: [null as number | null, [Validators.required]],
    coleccion_id: [null as number | null, [Validators.required]],
  });

  constructor() {
    this.panelService.temporadas().subscribe({ next: (t) => this.temporadas.set(t) });

    this.form.controls.temporada_id.valueChanges.subscribe((temporadaId) => {
      this.form.controls.coleccion_id.setValue(null);
      this.cargarColecciones(temporadaId);
    });

    effect(() => {
      if (!this.open()) {
        return;
      }
      const producto = this.producto();
      if (producto) {
        this.form.reset(
          {
            nombre: producto.nombre,
            descripcion: producto.descripcion ?? '',
            temporada_id: producto.temporada.id,
            coleccion_id: producto.coleccion.id,
          },
          { emitEvent: false },
        );
        this.cargarColecciones(producto.temporada.id);
      } else {
        this.form.reset(
          { nombre: '', descripcion: '', temporada_id: null, coleccion_id: null },
          { emitEvent: false },
        );
        this.colecciones.set([]);
      }

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  private cargarColecciones(temporadaId: number | null): void {
    if (temporadaId == null) {
      this.colecciones.set([]);
      return;
    }
    this.panelService.colecciones(temporadaId).subscribe({ next: (c) => this.colecciones.set(c) });
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
      temporada_id: value.temporada_id as number,
      coleccion_id: value.coleccion_id as number,
    });
  }
}
