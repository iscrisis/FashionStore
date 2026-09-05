import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { Icon } from '../../../../core/ui/icon/icon';
import { CiudadPublica, SucursalPublica } from '../../sucursales/sucursal.model';
import { SucursalPublicaService } from '../../sucursales/sucursal.service';
import { ProductoPublico } from '../catalogo.model';
import { CatalogoService } from '../catalogo.service';

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

  // Disponibilidad en tiendas (CU07 -- Ciudad -> Sucursales, reutilizado tal
  // cual, sin Departamento y sin stock; eso lo agregará CU12 más adelante).
  protected readonly ciudades = signal<CiudadPublica[]>([]);
  protected readonly sucursales = signal<SucursalPublica[]>([]);
  protected readonly ciudadId = signal<number | null>(null);
  protected readonly loadingCiudades = signal(true);
  protected readonly loadingSucursales = signal(false);
  protected readonly errorSucursales = signal<string | null>(null);

  constructor() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.catalogoService.getProducto(id).subscribe({
      next: (producto) => {
        this.producto.set(producto);
        this.imagenActivaUrl.set(producto.imagen_principal_url);
        this.tallaSeleccionadaId.set(producto.tallas[0]?.id ?? null);
        this.colorSeleccionadoId.set(producto.colores[0]?.id ?? null);
        this.loading.set(false);
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
          this.loadSucursales();
        }
      },
      error: () => {
        this.loadingCiudades.set(false);
        this.errorSucursales.set('No se pudieron cargar las ciudades. Inténtalo nuevamente.');
      },
    });
  }

  onCiudadChange(value: string): void {
    this.ciudadId.set(value ? Number(value) : null);
    this.loadSucursales();
  }

  loadSucursales(): void {
    const ciudadId = this.ciudadId();
    if (!ciudadId) {
      this.sucursales.set([]);
      return;
    }
    this.loadingSucursales.set(true);
    this.errorSucursales.set(null);
    this.sucursalService.listSucursales(ciudadId).subscribe({
      next: (sucursales) => {
        this.sucursales.set(sucursales);
        this.loadingSucursales.set(false);
      },
      error: () => {
        this.loadingSucursales.set(false);
        this.sucursales.set([]);
        this.errorSucursales.set('No se pudieron cargar las sucursales. Inténtalo nuevamente.');
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
  }

  seleccionarColor(id: number): void {
    this.colorSeleccionadoId.set(id);
  }
}
