import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { Icon } from '../../../core/ui/icon/icon';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { SucursalDelEncargado } from '../shared/panel-encargado.model';
import { PanelEncargadoService } from '../shared/panel-encargado.service';
import {
  LineaResumen,
  ProductoParaRecepcion,
  ProveedorResumen,
  RecepcionOut,
} from './recepcion-mercaderia.model';
import { RecepcionMercaderiaService } from './recepcion-mercaderia.service';

/**
 * CU15 -- Registrar recepción de mercadería (Panel del Encargado).
 *
 * La sucursal SOLO se muestra como información (viene de CU14, GET
 * mi-sucursal, en solo lectura) -- nunca es un selector, y nunca se envía en
 * el POST: el backend siempre la resuelve del usuario autenticado (ver
 * recepcion-mercaderia.service.ts / RegistrarRecepcionPayload).
 *
 * Flujo: elegir proveedor -> ver SUS productos reales del catálogo (no
 * propuestas ProductoProveedor sin aprobar) -> abrir un producto -> ingresar
 * cantidades por variante -> "Agregar a recepción" arma un resumen en
 * pantalla -> "Confirmar recepción" envía todo el resumen en un solo POST
 * (una sola transacción en backend, ver CU15 service.py).
 */
@Component({
  selector: 'app-recepcion-mercaderia',
  imports: [FormsModule, Icon],
  templateUrl: './recepcion-mercaderia.html',
  styleUrl: './recepcion-mercaderia.scss',
})
export class RecepcionMercaderia {
  private readonly panelEncargadoService = inject(PanelEncargadoService);
  private readonly recepcionService = inject(RecepcionMercaderiaService);
  private readonly toast = inject(ToastService);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly sucursal = signal<SucursalDelEncargado | null>(null);

  protected readonly proveedores = signal<ProveedorResumen[]>([]);
  protected readonly loadingProveedores = signal(true);
  protected readonly errorProveedores = signal<string | null>(null);
  protected readonly proveedorSeleccionadoId = signal<number | null>(null);

  protected readonly productos = signal<ProductoParaRecepcion[]>([]);
  protected readonly loadingProductos = signal(false);
  protected readonly errorProductos = signal<string | null>(null);
  protected readonly busquedaProducto = signal('');

  protected readonly productoSeleccionado = signal<ProductoParaRecepcion | null>(null);
  protected readonly cantidadesEditadas = signal<Record<number, number>>({});

  protected readonly resumen = signal<LineaResumen[]>([]);
  protected readonly observacion = signal('');
  protected readonly submitting = signal(false);
  protected readonly resultado = signal<RecepcionOut | null>(null);

  constructor() {
    this.panelEncargadoService.miSucursal().subscribe({ next: (s) => this.sucursal.set(s) });
    this.cargarProveedores();
  }

  cargarProveedores(): void {
    this.loadingProveedores.set(true);
    this.errorProveedores.set(null);
    this.recepcionService.listarProveedores().subscribe({
      next: (proveedores) => {
        this.proveedores.set(proveedores);
        this.loadingProveedores.set(false);
      },
      error: () => {
        this.loadingProveedores.set(false);
        this.errorProveedores.set('No se pudo conectar con el servidor. Inténtalo nuevamente.');
      },
    });
  }

  get proveedorSeleccionado(): ProveedorResumen | null {
    const id = this.proveedorSeleccionadoId();
    return this.proveedores().find((p) => p.id === id) ?? null;
  }

  onProveedorChange(value: string): void {
    const id = value ? Number(value) : null;
    this.proveedorSeleccionadoId.set(id);
    this.productos.set([]);
    this.busquedaProducto.set('');
    this.productoSeleccionado.set(null);
    this.cantidadesEditadas.set({});
    this.resumen.set([]);

    if (id == null) {
      return;
    }
    this.loadingProductos.set(true);
    this.errorProductos.set(null);
    this.recepcionService.listarProductosDelProveedor(id).subscribe({
      next: (productos) => {
        this.productos.set(productos);
        this.loadingProductos.set(false);
      },
      error: () => {
        this.loadingProductos.set(false);
        this.productos.set([]);
        this.errorProductos.set('No se pudo cargar los productos de este proveedor.');
      },
    });
  }

  onBusquedaChange(value: string): void {
    this.busquedaProducto.set(value);
  }

  get productosFiltrados(): ProductoParaRecepcion[] {
    const termino = this.busquedaProducto().trim().toLowerCase();
    if (!termino) {
      return this.productos();
    }
    return this.productos().filter((p) => p.nombre.toLowerCase().includes(termino));
  }

  abrirProducto(producto: ProductoParaRecepcion): void {
    this.productoSeleccionado.set(producto);
    const previas: Record<number, number> = {};
    for (const variante of producto.variantes) {
      const linea = this.resumen().find((l) => l.varianteId === variante.id);
      previas[variante.id] = linea?.cantidad ?? 0;
    }
    this.cantidadesEditadas.set(previas);
  }

  cerrarProducto(): void {
    this.productoSeleccionado.set(null);
    this.cantidadesEditadas.set({});
  }

  cantidadEditada(varianteId: number): number {
    return this.cantidadesEditadas()[varianteId] ?? 0;
  }

  onCantidadChange(varianteId: number, valor: string): void {
    const numero = Math.trunc(Number(valor));
    const segura = Number.isFinite(numero) && numero >= 0 ? numero : 0;
    this.cantidadesEditadas.update((mapa) => ({ ...mapa, [varianteId]: segura }));
  }

  agregarARecepcion(producto: ProductoParaRecepcion): void {
    const cantidades = this.cantidadesEditadas();
    const nuevasLineas: LineaResumen[] = [];
    for (const variante of producto.variantes) {
      const cantidad = cantidades[variante.id] ?? 0;
      if (cantidad > 0) {
        nuevasLineas.push({
          productoId: producto.id,
          productoNombre: producto.nombre,
          varianteId: variante.id,
          tallaNombre: variante.talla.nombre,
          colorNombre: variante.color.nombre,
          cantidad,
        });
      }
    }

    if (nuevasLineas.length === 0) {
      this.toast.error('Ingresa al menos una cantidad mayor a 0.');
      return;
    }

    this.resumen.update((actual) => {
      const sinEsteProducto = actual.filter((l) => l.productoId !== producto.id);
      return [...sinEsteProducto, ...nuevasLineas];
    });
    this.toast.success(`${producto.nombre} agregado a la recepción.`);
    this.cerrarProducto();
  }

  quitarLinea(varianteId: number): void {
    this.resumen.update((actual) => actual.filter((l) => l.varianteId !== varianteId));
  }

  get totalUnidades(): number {
    return this.resumen().reduce((acc, l) => acc + l.cantidad, 0);
  }

  onObservacionChange(value: string): void {
    this.observacion.set(value);
  }

  confirmarRecepcion(): void {
    const proveedorId = this.proveedorSeleccionadoId();
    const lineas = this.resumen();
    if (proveedorId == null || lineas.length === 0) {
      this.toast.error('Agrega al menos una variante antes de confirmar.');
      return;
    }

    this.submitting.set(true);
    this.recepcionService
      .registrar({
        proveedor_id: proveedorId,
        observacion: this.observacion().trim() || null,
        detalles: lineas.map((l) => ({
          producto_id: l.productoId,
          producto_variante_id: l.varianteId,
          cantidad_recibida: l.cantidad,
        })),
      })
      .subscribe({
        next: (out) => {
          this.submitting.set(false);
          this.resultado.set(out);
          this.resumen.set([]);
          this.observacion.set('');
          this.toast.success('Recepción registrada correctamente.');
        },
        error: (err) => {
          this.submitting.set(false);
          const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
          this.toast.error(detalle ?? 'No se pudo registrar la recepción. Intenta nuevamente.');
        },
      });
  }

  registrarOtra(): void {
    this.resultado.set(null);
    this.proveedorSeleccionadoId.set(null);
    this.productos.set([]);
    this.busquedaProducto.set('');
    this.productoSeleccionado.set(null);
    this.cantidadesEditadas.set({});
  }
}
