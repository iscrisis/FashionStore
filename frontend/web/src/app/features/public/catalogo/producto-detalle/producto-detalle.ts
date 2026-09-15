import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { Icon } from '../../../../core/ui/icon/icon';
import { CiudadPublica } from '../../sucursales/sucursal.model';
import { SucursalPublicaService } from '../../sucursales/sucursal.service';
import { ProductoPublico } from '../catalogo.model';
import { CatalogoService } from '../catalogo.service';
import { DisponibilidadSucursal } from './disponibilidad.model';
import { DisponibilidadService } from './disponibilidad.service';

@Component({
  selector: 'app-producto-detalle',
  imports: [RouterLink, Icon, FormsModule],
  templateUrl: './producto-detalle.html',
  styleUrl: './producto-detalle.scss',
})
export class ProductoDetalle {
  private readonly route = inject(ActivatedRoute);
  private readonly catalogoService = inject(CatalogoService);
  private readonly sucursalService = inject(SucursalPublicaService);
  private readonly disponibilidadService = inject(DisponibilidadService);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly producto = signal<ProductoPublico | null>(null);
  protected readonly loading = signal(true);
  protected readonly notFound = signal(false);

  protected readonly imagenActivaUrl = signal<string | null>(null);
  protected readonly tallaSeleccionadaId = signal<number | null>(null);
  protected readonly colorSeleccionadoId = signal<number | null>(null);
  // Si una imagen referenciada ya no existe físicamente (ej. archivo perdido),
  // se marca aquí para caer al ícono de reserva en vez del roto nativo del navegador.
  protected readonly erroredUrls = signal<ReadonlySet<string>>(new Set());

  // Disponibilidad en tiendas -- CU12: por cada sucursal, trae todas las
  // variantes (talla+color) activas del producto con su stock real (ver
  // ProductoDisponibilidad). Aquí se guarda solo el array de sucursales
  // (`.disponibilidad`), que es lo que consume la plantilla. La lista de
  // ciudades sigue viniendo de CU07 (reutilizada, no duplicada).
  protected readonly ciudades = signal<CiudadPublica[]>([]);
  protected readonly disponibilidad = signal<DisponibilidadSucursal[]>([]);
  protected readonly ciudadId = signal<number | null>(null);
  protected readonly loadingCiudades = signal(true);
  protected readonly loadingDisponibilidad = signal(false);
  protected readonly errorDisponibilidad = signal<string | null>(null);

  constructor() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.catalogoService.getProducto(id).subscribe({
      next: (producto) => {
        this.producto.set(producto);
        this.imagenActivaUrl.set(producto.imagen_principal_url);
        this.tallaSeleccionadaId.set(producto.tallas[0]?.id ?? null);
        this.colorSeleccionadoId.set(producto.colores[0]?.id ?? null);
        this.loading.set(false);
        this.loadDisponibilidad();
      },
      error: () => {
        this.loading.set(false);
        this.notFound.set(true);
      },
    });

    this.sucursalService.listCiudades().subscribe({
      next: (ciudades) => {
        this.ciudades.set(ciudades);
        this.loadingCiudades.set(false);
        if (ciudades.length > 0) {
          this.ciudadId.set(ciudades[0].id);
          this.loadDisponibilidad();
        }
      },
      error: () => {
        this.loadingCiudades.set(false);
        this.errorDisponibilidad.set('No se pudieron cargar las ciudades. Inténtalo nuevamente.');
      },
    });
  }

  onCiudadChange(value: string): void {
    this.ciudadId.set(value ? Number(value) : null);
    this.loadDisponibilidad();
  }

  loadDisponibilidad(): void {
    const producto = this.producto();
    const tallaId = this.tallaSeleccionadaId();
    const colorId = this.colorSeleccionadoId();
    const ciudadId = this.ciudadId();
    // Requiere producto + talla + color + ciudad ya resueltos -- el
    // producto y las ciudades cargan en paralelo, así que cada uno dispara
    // esta carga al terminar y el que llegue primero simplemente no hace nada.
    if (!producto || !tallaId || !colorId || !ciudadId) {
      return;
    }

    this.loadingDisponibilidad.set(true);
    this.errorDisponibilidad.set(null);
    this.disponibilidadService.consultar(producto.id, tallaId, colorId, ciudadId).subscribe({
      next: (respuesta) => {
        this.disponibilidad.set(respuesta.disponibilidad);
        this.loadingDisponibilidad.set(false);
      },
      error: () => {
        this.loadingDisponibilidad.set(false);
        this.disponibilidad.set([]);
        this.errorDisponibilidad.set('No se pudo consultar la disponibilidad. Inténtalo nuevamente.');
      },
    });
  }

  protected get galeria(): string[] {
    const producto = this.producto();
    if (!producto) {
      return [];
    }
    const adicionales = producto.imagenes.map((imagen) => imagen.url);
    return producto.imagen_principal_url
      ? [producto.imagen_principal_url, ...adicionales]
      : adicionales;
  }

  seleccionarImagen(url: string): void {
    this.imagenActivaUrl.set(url);
  }

  marcarImagenRota(url: string): void {
    this.erroredUrls.update((actuales) => new Set(actuales).add(url));
  }

  seleccionarTalla(id: number): void {
    this.tallaSeleccionadaId.set(id);
    this.loadDisponibilidad();
  }

  seleccionarColor(id: number): void {
    this.colorSeleccionadoId.set(id);
    this.loadDisponibilidad();
  }
}
