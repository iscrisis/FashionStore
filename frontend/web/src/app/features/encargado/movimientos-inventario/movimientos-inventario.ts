import { DatePipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { Icon } from '../../../core/ui/icon/icon';
import { ToastService } from '../../../core/ui/toast/toast.service';
import {
  MovimientoOut,
  ProductoConVariantes,
  TipoMovimiento,
  VarianteConStock,
} from './movimientos-inventario.model';
import { MovimientosInventarioService } from './movimientos-inventario.service';

/**
 * CU16 -- Registrar movimientos de inventario (Panel del Encargado).
 *
 * Distinto de CU15 (recepción de mercadería de un proveedor): aquí el
 * Encargado registra un AJUSTE manual y justificado (positivo o negativo) --
 * ej. una prenda dañada, o unidades de más encontradas en un conteo físico.
 * La suma/resta y el rechazo de stock negativo ocurren SIEMPRE en el backend
 * (ver CU16 service.py); esta pantalla solo envía la intención.
 *
 * Flujo: buscar producto -> elegir variante real -> ver su stock actual ->
 * elegir AJUSTE POSITIVO/NEGATIVO -> cantidad -> motivo obligatorio ->
 * confirmar. Puede llegar con ?productoId=&varianteId= desde el botón
 * "Registrar movimiento" de CU14 (inventario.ts) para preseleccionar.
 *
 * El historial de abajo es de SU sucursal únicamente -- el backend la
 * resuelve siempre del usuario autenticado, nunca de esta pantalla.
 */
@Component({
  selector: 'app-movimientos-inventario',
  imports: [FormsModule, Icon, DatePipe],
  templateUrl: './movimientos-inventario.html',
  styleUrl: './movimientos-inventario.scss',
})
export class MovimientosInventario {
  private readonly service = inject(MovimientosInventarioService);
  private readonly toast = inject(ToastService);
  private readonly route = inject(ActivatedRoute);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly productos = signal<ProductoConVariantes[]>([]);
  protected readonly loadingProductos = signal(true);
  protected readonly errorProductos = signal<string | null>(null);
  protected readonly busqueda = signal('');

  protected readonly productoSeleccionado = signal<ProductoConVariantes | null>(null);
  protected readonly varianteSeleccionada = signal<VarianteConStock | null>(null);

  protected readonly tipo = signal<TipoMovimiento>('AJUSTE_POSITIVO');
  protected readonly cantidad = signal(0);
  protected readonly motivo = signal('');
  protected readonly submitting = signal(false);
  protected readonly resultado = signal<MovimientoOut | null>(null);

  protected readonly historial = signal<MovimientoOut[]>([]);
  protected readonly loadingHistorial = signal(true);

  private searchDebounce?: ReturnType<typeof setTimeout>;
  private productoIdPreseleccionado: number | null = null;
  private varianteIdPreseleccionada: number | null = null;

  constructor() {
    const productoParam = this.route.snapshot.queryParamMap.get('productoId');
    if (productoParam) {
      this.productoIdPreseleccionado = Number(productoParam);
    }
    const varianteParam = this.route.snapshot.queryParamMap.get('varianteId');
    if (varianteParam) {
      this.varianteIdPreseleccionada = Number(varianteParam);
    }

    this.cargarProductos();
    this.cargarHistorial();
  }

  cargarProductos(): void {
    this.loadingProductos.set(true);
    this.errorProductos.set(null);
    this.service.buscarProductos(this.busqueda() || undefined).subscribe({
      next: (productos) => {
        this.productos.set(productos);
        this.loadingProductos.set(false);
        this.aplicarPreseleccion();
      },
      error: () => {
        this.loadingProductos.set(false);
        this.productos.set([]);
        this.errorProductos.set('No se pudo conectar con el servidor. Inténtalo nuevamente.');
      },
    });
  }

  private aplicarPreseleccion(): void {
    if (this.productoIdPreseleccionado == null) {
      return;
    }
    const producto = this.productos().find((p) => p.id === this.productoIdPreseleccionado);
    if (!producto) {
      return;
    }
    this.seleccionarProducto(producto);
    if (this.varianteIdPreseleccionada != null) {
      const variante = producto.variantes.find((v) => v.id === this.varianteIdPreseleccionada);
      if (variante) {
        this.seleccionarVariante(variante);
      }
    }
    this.productoIdPreseleccionado = null;
    this.varianteIdPreseleccionada = null;
  }

  cargarHistorial(): void {
    this.loadingHistorial.set(true);
    this.service.historial().subscribe({
      next: (movimientos) => {
        this.historial.set(movimientos);
        this.loadingHistorial.set(false);
      },
      error: () => {
        this.loadingHistorial.set(false);
      },
    });
  }

  onBusquedaChange(value: string): void {
    this.busqueda.set(value);
    clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => this.cargarProductos(), 350);
  }

  seleccionarProducto(producto: ProductoConVariantes): void {
    this.productoSeleccionado.set(producto);
    this.varianteSeleccionada.set(null);
    this.resultado.set(null);
  }

  seleccionarVariante(variante: VarianteConStock): void {
    this.varianteSeleccionada.set(variante);
    this.resultado.set(null);
  }

  onTipoChange(tipo: TipoMovimiento): void {
    this.tipo.set(tipo);
  }

  onCantidadChange(valor: string): void {
    const numero = Math.trunc(Number(valor));
    this.cantidad.set(Number.isFinite(numero) && numero > 0 ? numero : 0);
  }

  onMotivoChange(value: string): void {
    this.motivo.set(value);
  }

  get puedeConfirmar(): boolean {
    return (
      this.varianteSeleccionada() != null &&
      this.cantidad() > 0 &&
      this.motivo().trim().length >= 3 &&
      !this.submitting()
    );
  }

  confirmar(): void {
    const variante = this.varianteSeleccionada();
    if (!variante || !this.puedeConfirmar) {
      return;
    }

    this.submitting.set(true);
    this.service
      .registrar({
        producto_variante_id: variante.id,
        tipo: this.tipo(),
        cantidad: this.cantidad(),
        motivo: this.motivo().trim(),
      })
      .subscribe({
        next: (out) => {
          this.submitting.set(false);
          this.resultado.set(out);
          this.toast.success('Movimiento registrado correctamente.');

          // Refleja el nuevo stock en la variante ya cargada, sin recargar
          // toda la lista de productos.
          this.productos.update((lista) =>
            lista.map((p) =>
              p.id !== out.producto.id
                ? p
                : {
                    ...p,
                    variantes: p.variantes.map((v) =>
                      v.id === out.variante.id ? { ...v, cantidad: out.stock_resultante } : v,
                    ),
                  },
            ),
          );
          this.varianteSeleccionada.update((v) =>
            v && v.id === out.variante.id ? { ...v, cantidad: out.stock_resultante } : v,
          );
          this.cantidad.set(0);
          this.motivo.set('');
          this.cargarHistorial();
        },
        error: (err) => {
          this.submitting.set(false);
          const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
          this.toast.error(detalle ?? 'No se pudo registrar el movimiento. Intenta nuevamente.');
        },
      });
  }

  registrarOtro(): void {
    this.resultado.set(null);
    this.productoSeleccionado.set(null);
    this.varianteSeleccionada.set(null);
    this.tipo.set('AJUSTE_POSITIVO');
    this.cantidad.set(0);
    this.motivo.set('');
  }
}
