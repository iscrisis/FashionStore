import { Component, effect, inject, input, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Coleccion, ColeccionPayload, Temporada } from '../../temporada-coleccion.model';
import { ColeccionAdminService } from '../../coleccion-admin.service';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { Icon } from '../../../../core/ui/icon/icon';

const FORMATOS_IMAGEN_PERMITIDOS = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
const TAMANO_MAXIMO_IMAGEN_BYTES = 5 * 1024 * 1024;

@Component({
  selector: 'app-coleccion-form',
  imports: [ReactiveFormsModule, Icon],
  templateUrl: './coleccion-form.html',
  styleUrl: './coleccion-form.scss',
})
export class ColeccionForm {
  readonly open = input(false);
  readonly coleccion = input<Coleccion | null>(null);
  readonly temporadas = input<Temporada[]>([]);
  readonly readonly = input(false);
  readonly submitting = input(false);

  readonly save = output<ColeccionPayload>();
  readonly close = output<void>();
  // Marcar/desmarcar como destacada afecta a OTRA fila de la tabla (deja de
  // estarlo), así que el padre necesita recargar el listado -- este cambio
  // no pasa por el formulario/`save`, se aplica al instante como la imagen.
  readonly refresh = output<void>();

  private readonly fb = inject(FormBuilder);
  private readonly coleccionService = inject(ColeccionAdminService);

  protected readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(120)]],
    temporada_id: [null as number | null, [Validators.required]],
    descripcion: [''],
    is_active: [true],
  });

  protected readonly esDestacada = signal(false);
  protected readonly actualizandoDestacada = signal(false);
  protected readonly imagenDestacadaUrl = signal<string | null>(null);
  protected readonly subiendoImagen = signal(false);
  protected readonly imagenError = signal<string | null>(null);
  protected readonly resolveMediaUrl = resolveMediaUrl;

  constructor() {
    effect(() => {
      if (!this.open()) {
        return;
      }
      const coleccion = this.coleccion();
      this.imagenError.set(null);
      if (coleccion) {
        this.form.reset({
          nombre: coleccion.nombre,
          temporada_id: coleccion.temporada.id,
          descripcion: coleccion.descripcion ?? '',
          is_active: coleccion.is_active,
        });
        this.esDestacada.set(coleccion.es_destacada_inicio);
        this.imagenDestacadaUrl.set(coleccion.imagen_destacada_url);
      } else {
        this.form.reset({ nombre: '', temporada_id: null, descripcion: '', is_active: true });
        this.esDestacada.set(false);
        this.imagenDestacadaUrl.set(null);
      }

      if (this.readonly()) {
        this.form.disable();
      } else {
        this.form.enable();
      }
    });
  }

  protected get isEditMode(): boolean {
    return this.coleccion() !== null;
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
      temporada_id: value.temporada_id as number,
      descripcion: value.descripcion.trim() || null,
      is_active: value.is_active,
    });
  }

  onDestacadaChange(event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    const coleccion = this.coleccion();
    if (!coleccion) {
      return;
    }
    this.actualizandoDestacada.set(true);
    this.coleccionService.setDestacadaInicio(coleccion.id, checked).subscribe({
      next: (actualizada) => {
        this.actualizandoDestacada.set(false);
        this.esDestacada.set(actualizada.es_destacada_inicio);
        this.refresh.emit();
      },
      error: () => {
        this.actualizandoDestacada.set(false);
        this.esDestacada.set(!checked);
      },
    });
  }

  onImagenSeleccionada(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0];
    input.value = '';
    const coleccion = this.coleccion();
    if (!archivo || !coleccion) {
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
    this.coleccionService.setImagenDestacada(coleccion.id, archivo).subscribe({
      next: (actualizada) => {
        this.subiendoImagen.set(false);
        this.imagenDestacadaUrl.set(actualizada.imagen_destacada_url);
        this.refresh.emit();
      },
      error: () => {
        this.subiendoImagen.set(false);
        this.imagenError.set('No se pudo cargar la imagen. Intenta nuevamente.');
      },
    });
  }
}
