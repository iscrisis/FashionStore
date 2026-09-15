import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { Icon } from '../../../core/ui/icon/icon';
import {
  CategoriaResumen,
  ColeccionConTemporadaResumen,
  ProductoInventario,
  SucursalDelEncargado,
} from '../shared/panel-encargado.model';
import { PanelEncargadoService } from '../shared/panel-encargado.service';

// Agrupación puramente de presentación: Colección -> Categoría -> Producto.
// Se arma en el componente a partir de la misma lista plana que ya devuelve
// CU14 (cada producto ya trae su categoria/coleccion, ver panel-encargado.model.ts)
// -- no es un contrato del backend, así que no requiere un endpoint nuevo.
//
// coleccion/categoria se tratan como posiblemente ausentes (null) aquí a
// propósito: es una tolerancia puramente defensiva del frontend, no porque
// el modelo real lo permita (Producto.categoria_id/coleccion_id son
// NOT NULL en la base de datos -- CU08 no deja crear un producto sin
// ambos). Cubre el caso de una respuesta que no venga con esos campos
// (p. ej. una versión de API desactualizada) sin que la pantalla completa
// se rompa: el producto igual debe aparecer.
interface GrupoCategoria {
  categoriaId: number | null;
  categoria: CategoriaResumen | null;
  productos: ProductoInventario[];
}

interface GrupoColeccion {
  coleccionId: number | null;
  coleccion: ColeccionConTemporadaResumen | null;
  categorias: GrupoCategoria[];
  totalProductos: number;
}

/**
 * Inventario del Encargado -- CONSULTA de solo lectura del stock por
 * variante (talla+color) de SU sucursal, siempre resuelta por el backend
 * desde el usuario autenticado. Productos y variantes vienen de CU08.
 *
 * Ya no edita el stock directamente: ese botón +/- sin trazabilidad fue
 * reemplazado por "Registrar movimiento", que navega a CU16
 * (movimientos-inventario) con la variante preseleccionada -- todo ajuste
 * de stock queda registrado con motivo y usuario ahí, nunca aquí.
 *
 * La lista se organiza en árbol (Colección -> Categoría -> Producto) para
 * que un catálogo grande siga siendo navegable -- todo colapsado por
 * defecto, el Encargado abre solo lo que necesita.
 */
@Component({
  selector: 'app-inventario',
  imports: [FormsModule, Icon],
  templateUrl: './inventario.html',
  styleUrl: './inventario.scss',
})
export class Inventario {
  private readonly panelService = inject(PanelEncargadoService);
  private readonly router = inject(Router);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly sucursal = signal<SucursalDelEncargado | null>(null);
  protected readonly productos = signal<ProductoInventario[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly searchTerm = signal('');

  // Estado de expansión del árbol -- todo cerrado por defecto (ninguna
  // colección/categoría/producto se abre automáticamente al cargar).
  // Categoría se identifica con "coleccionId:categoriaId" porque una misma
  // categoría (p. ej. "Poleras") puede repetirse en varias colecciones.
  private readonly coleccionesAbiertas = signal<ReadonlySet<number | null>>(new Set());
  private readonly categoriasAbiertas = signal<ReadonlySet<string>>(new Set());
  private readonly productosAbiertos = signal<ReadonlySet<number>>(new Set());

  private searchDebounce?: ReturnType<typeof setTimeout>;

  constructor() {
    this.panelService.miSucursal().subscribe({ next: (sucursal) => this.sucursal.set(sucursal) });
    this.load();
  }

  onSearchChange(value: string): void {
    this.searchTerm.set(value);
    clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => this.load(), 350);
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.panelService.listarInventario(this.searchTerm() || undefined).subscribe({
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

  protected get gruposColeccion(): GrupoColeccion[] {
    const porColeccion = new Map<number | null, GrupoColeccion>();

    for (const producto of this.productos()) {
      const coleccion = producto.coleccion ?? null;
      const coleccionId = coleccion?.id ?? null;

      let grupoColeccion = porColeccion.get(coleccionId);
      if (!grupoColeccion) {
        grupoColeccion = { coleccionId, coleccion, categorias: [], totalProductos: 0 };
        porColeccion.set(coleccionId, grupoColeccion);
      }
      grupoColeccion.totalProductos++;

      const categoria = producto.categoria ?? null;
      const categoriaId = categoria?.id ?? null;

      let grupoCategoria = grupoColeccion.categorias.find((c) => c.categoriaId === categoriaId);
      if (!grupoCategoria) {
        grupoCategoria = { categoriaId, categoria, productos: [] };
        grupoColeccion.categorias.push(grupoCategoria);
      }
      grupoCategoria.productos.push(producto);
    }

    const grupos = [...porColeccion.values()];
    for (const grupo of grupos) {
      grupo.categorias.sort((a, b) =>
        (a.categoria?.nombre ?? '').localeCompare(b.categoria?.nombre ?? ''),
      );
    }
    return grupos.sort((a, b) => (a.coleccion?.nombre ?? '').localeCompare(b.coleccion?.nombre ?? ''));
  }

  private claveCategoria(coleccionId: number | null, categoriaId: number | null): string {
    return `${coleccionId}:${categoriaId}`;
  }

  coleccionAbierta(coleccionId: number | null): boolean {
    return this.coleccionesAbiertas().has(coleccionId);
  }

  categoriaAbierta(coleccionId: number | null, categoriaId: number | null): boolean {
    return this.categoriasAbiertas().has(this.claveCategoria(coleccionId, categoriaId));
  }

  productoAbierto(productoId: number): boolean {
    return this.productosAbiertos().has(productoId);
  }

  toggleColeccion(coleccionId: number | null): void {
    this.coleccionesAbiertas.update((actuales) => {
      const nuevo = new Set(actuales);
      if (nuevo.has(coleccionId)) {
        nuevo.delete(coleccionId);
      } else {
        nuevo.add(coleccionId);
      }
      return nuevo;
    });
  }

  toggleCategoria(coleccionId: number | null, categoriaId: number | null): void {
    const clave = this.claveCategoria(coleccionId, categoriaId);
    this.categoriasAbiertas.update((actuales) => {
      const nuevo = new Set(actuales);
      if (nuevo.has(clave)) {
        nuevo.delete(clave);
      } else {
        nuevo.add(clave);
      }
      return nuevo;
    });
  }

  toggleProducto(productoId: number): void {
    this.productosAbiertos.update((actuales) => {
      const nuevo = new Set(actuales);
      if (nuevo.has(productoId)) {
        nuevo.delete(productoId);
      } else {
        nuevo.add(productoId);
      }
      return nuevo;
    });
  }

  registrarMovimiento(producto: ProductoInventario, varianteId: number): void {
    this.router.navigate(['/encargado/movimientos-inventario'], {
      queryParams: { productoId: producto.id, varianteId },
    });
  }
}
