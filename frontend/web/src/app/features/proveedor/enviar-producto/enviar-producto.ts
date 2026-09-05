import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { ColeccionResumen, TemporadaResumen } from '../shared/panel-proveedor.model';
import { PanelProveedorService } from '../shared/panel-proveedor.service';

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

  protected readonly temporadas = signal<TemporadaResumen[]>([]);
  protected readonly colecciones = signal<ColeccionResumen[]>([]);
  protected readonly submitting = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(150)]],
    descripcion: [''],
    temporada_id: [null as number | null, [Validators.required]],
    coleccion_id: [null as number | null, [Validators.required]],
    disponibilidad: [true],
  });

  constructor() {
    this.panelService.temporadas().subscribe({ next: (t) => this.temporadas.set(t) });

    this.form.controls.temporada_id.valueChanges.subscribe((temporadaId) => {
      this.form.controls.coleccion_id.setValue(null);
      if (temporadaId == null) {
        this.colecciones.set([]);
        return;
      }
      this.panelService.colecciones(temporadaId).subscribe({ next: (c) => this.colecciones.set(c) });
    });
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
        temporada_id: value.temporada_id as number,
        coleccion_id: value.coleccion_id as number,
        disponibilidad: value.disponibilidad,
      })
      .subscribe({
        next: () => {
          this.submitting.set(false);
          this.toast.success('Producto enviado correctamente.');
          this.router.navigateByUrl('/proveedor/mis-productos');
        },
        error: (err) => {
          this.submitting.set(false);
          if (err.status === 422) {
            this.toast.error('Revisa la temporada y la colección seleccionadas.');
          } else {
            this.toast.error('No se pudo enviar el producto. Intenta nuevamente.');
          }
        },
      });
  }
}
