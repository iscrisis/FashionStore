import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import {
  CategoriaPublica,
  ColeccionPublica,
  ColorPublico,
  ProductoPublico,
  TallaPublica,
} from '../catalogo.model';
import { CatalogoService } from '../catalogo.service';
import { ProductCard } from '../../home/product-card/product-card';

@Component({
  selector: 'app-catalogo-page',
  imports: [FormsModule, ProductCard],
  templateUrl: './catalogo-page.html',
  styleUrl: './catalogo-page.scss',
})
export class CatalogoPage {
  private readonly catalogoService = inject(CatalogoService);
  private readonly route = inject(ActivatedRoute);

  protected readonly productos = signal<ProductoPublico[]>([]);
  protected readonly categorias = signal<CategoriaPublica[]>([]);
  protected readonly colecciones = signal<ColeccionPublica[]>([]);
  protected readonly tallas = signal<TallaPublica[]>([]);
  protected readonly colores = signal<ColorPublico[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly searchTerm = signal('');
  protected readonly categoriaId = signal<number | null>(null);
  protected readonly coleccionId = signal<number | null>(null);
  protected readonly tallaId = signal<number | null>(null);
  protected readonly colorId = signal<number | null>(null);

  private searchDebounce?: ReturnType<typeof setTimeout>;

  constructor() {
    this.catalogoService.listCategorias().subscribe((valores) => this.categorias.set(valores));
    this.catalogoService.listColecciones().subscribe((valores) => this.colecciones.set(valores));
    this.catalogoService.listTallas().subscribe((valores) => this.tallas.set(valores));
    this.catalogoService.listColores().subscribe((valores) => this.colores.set(valores));

    // Permite llegar con un filtro ya aplicado, ej. desde una tarjeta de categoría.
    const categoriaParam = this.route.snapshot.queryParamMap.get('categoria_id');
    if (categoriaParam) {
      this.categoriaId.set(Number(categoriaParam));
    }
    const coleccionParam = this.route.snapshot.queryParamMap.get('coleccion_id');
    if (coleccionParam) {
      this.coleccionId.set(Number(coleccionParam));
    }

    this.load();
  }

  onSearchChange(value: string): void {
    this.searchTerm.set(value);
    clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => this.load(), 350);
  }

  onCategoriaChange(value: string): void {
    this.categoriaId.set(value ? Number(value) : null);
    this.load();
  }

  onColeccionChange(value: string): void {
    this.coleccionId.set(value ? Number(value) : null);
    this.load();
  }

  onTallaChange(value: string): void {
    this.tallaId.set(value ? Number(value) : null);
    this.load();
  }

  onColorChange(value: string): void {
    this.colorId.set(value ? Number(value) : null);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.catalogoService
      .listProductos({
        search: this.searchTerm() || undefined,
        categoria_id: this.categoriaId() ?? undefined,
        coleccion_id: this.coleccionId() ?? undefined,
        talla_id: this.tallaId() ?? undefined,
        color_id: this.colorId() ?? undefined,
      })
      .subscribe({
        next: (productos) => {
          this.productos.set(productos);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.productos.set([]);
          this.errorMessage.set('No se pudo conectar con el servidor. Inténtalo nuevamente.');
        },
      });
  }
}
