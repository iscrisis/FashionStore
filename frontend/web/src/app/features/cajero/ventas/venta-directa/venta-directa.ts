import { Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Icon } from '../../../../core/ui/icon/icon';
import { ToastService } from '../../../../core/ui/toast/toast.service';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { ProcesarPago } from '../procesar-pago/procesar-pago';
import { VentaResumen } from '../venta-resumen/venta-resumen';
import { ProductoBusquedaOut, ProductoResumen, VarianteResumen, VentaPresencialOut } from '../venta-presencial.model';
import { VentaPresencialService } from '../venta-presencial.service';

interface LineaVenta {
  producto_variante_id: number;
  producto: ProductoResumen;
  variante: VarianteResumen;
  precio_unitario: number;
  en_promocion: boolean;
  porcentaje_descuento: number | null;
  disponible: number;
  cantidad: number;
}

type Paso = 'armando' | 'resumen';

/**
 * CU24 -- Registrar venta presencial (Cajero), flujo A: VENTA DIRECTA
 * ('/cajero/ventas/nueva', CAJERO autenticado -- ver app.routes.ts), a la
 * que lleva "Ventas" del sidebar (CajeroLayout) y el botón "+ NUEVA VENTA"
 * de la pantalla de reservas pendientes (reservas-pendientes.html) -- ese
 * botón NUNCA tuvo lógica de venta propia, solo navega aquí. Vive bajo
 * CajeroLayout -- ya NO trae su propia barra superior ni "Cerrar sesión",
 * ambos los da el layout.
 *
 * Dos pasos locales (sin ruta hija, mismo criterio que otros wizards de este
 * proyecto -- ver finalizar-compra.ts, CU22):
 *  1. 'armando'  -- el Cajero busca productos por nombre (SOLO
 *                    productos/variantes activas), agrega líneas
 *                    (producto+color+talla+cantidad) con su "Stock
 *                    disponible" informativo (`stock_actual -
 *                    stock_reservado` de SU sucursal), puede ajustar
 *                    cantidad o eliminar una línea. Nada de esto llama al
 *                    backend hasta "Registrar venta": es una lista local,
 *                    como un carrito de mostrador.
 *  2. 'resumen'  -- tras registrar, la Venta YA quedó creada
 *                    (PRESENCIAL/PENDIENTE_PAGO, código VT-00001) --
 *                    <app-venta-resumen> con [VOLVER] / [CONTINUAR AL PAGO].
 *
 * "Continuar al pago" abre <app-procesar-pago> (CU25) -- el MISMO modal que
 * usa reservas-pendientes.html para "Cargar venta", nunca uno propio (ver
 * procesar-pago.ts). Confirmado el pago, se vuelve al panel del Cajero.
 *
 * El total que se ve mientras se arma la venta es SOLO informativo (suma
 * local de precio_unitario × cantidad, con el precio que ya trajo la
 * búsqueda) -- el que manda es el que devuelve el backend al registrar,
 * nunca lo que Angular calculó.
 */
@Component({
  selector: 'app-venta-directa',
  imports: [Icon, VentaResumen, ProcesarPago],
  templateUrl: './venta-directa.html',
  styleUrl: './venta-directa.scss',
})
export class VentaDirecta {
  private readonly service = inject(VentaPresencialService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly paso = signal<Paso>('armando');

  protected readonly termino = signal('');
  protected readonly buscando = signal(false);
  protected readonly seBusco = signal(false);
  protected readonly resultados = signal<ProductoBusquedaOut[]>([]);

  protected readonly lineas = signal<LineaVenta[]>([]);
  protected readonly registrando = signal(false);
  protected readonly ventaCreada = signal<VentaPresencialOut | null>(null);
  protected readonly modalPagoAbierto = signal(false);

  protected readonly total = computed(() =>
    this.lineas().reduce((acumulado, linea) => acumulado + linea.precio_unitario * linea.cantidad, 0),
  );

  actualizarTermino(valor: string): void {
    this.termino.set(valor);
  }

  buscar(): void {
    const nombre = this.termino().trim();
    if (!nombre) {
      this.resultados.set([]);
      this.seBusco.set(false);
      return;
    }
    this.buscando.set(true);
    this.service.buscarProductos(nombre).subscribe({
      next: (resultados) => {
        this.resultados.set(resultados);
        this.buscando.set(false);
        this.seBusco.set(true);
      },
      error: () => {
        this.buscando.set(false);
        this.seBusco.set(true);
        this.resultados.set([]);
        this.toast.error('No se pudo buscar productos. Inténtalo nuevamente.');
      },
    });
  }

  agregarLinea(resultado: ProductoBusquedaOut): void {
    if (resultado.disponible <= 0) {
      return;
    }
    const yaExiste = this.lineas().some((l) => l.producto_variante_id === resultado.producto_variante_id);
    if (yaExiste) {
      this._incrementarPorId(resultado.producto_variante_id);
      return;
    }
    this.lineas.update((lineas) => [
      ...lineas,
      {
        producto_variante_id: resultado.producto_variante_id,
        producto: resultado.producto,
        variante: resultado.variante,
        precio_unitario: resultado.precio_unitario,
        en_promocion: resultado.en_promocion,
        porcentaje_descuento: resultado.porcentaje_descuento,
        disponible: resultado.disponible,
        cantidad: 1,
      },
    ]);
  }

  incrementar(linea: LineaVenta): void {
    this._incrementarPorId(linea.producto_variante_id);
  }

  decrementar(linea: LineaVenta): void {
    if (linea.cantidad <= 1) {
      return;
    }
    this.lineas.update((lineas) =>
      lineas.map((l) => (l.producto_variante_id === linea.producto_variante_id ? { ...l, cantidad: l.cantidad - 1 } : l)),
    );
  }

  eliminarLinea(linea: LineaVenta): void {
    this.lineas.update((lineas) => lineas.filter((l) => l.producto_variante_id !== linea.producto_variante_id));
  }

  registrarVenta(): void {
    if (this.lineas().length === 0 || this.registrando()) {
      return;
    }
    this.registrando.set(true);
    const payload = {
      items: this.lineas().map((l) => ({ producto_variante_id: l.producto_variante_id, cantidad: l.cantidad })),
    };
    this.service.crearVentaDirecta(payload).subscribe({
      next: (venta) => {
        this.registrando.set(false);
        this.ventaCreada.set(venta);
        this.paso.set('resumen');
      },
      error: (err) => {
        this.registrando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo registrar la venta. Inténtalo nuevamente.');
      },
    });
  }

  onVolverAlPanel(): void {
    this.router.navigateByUrl('/cajero/reservas-pendientes');
  }

  abrirModalPago(): void {
    this.modalPagoAbierto.set(true);
  }

  cerrarModalPago(): void {
    this.modalPagoAbierto.set(false);
  }

  onPagoRegistrado(): void {
    // El pago (CU25) ya quedó confirmado -- vuelve a la lista de reservas
    // para caja, igual que "Volver", nada más queda por hacer aquí.
    this.router.navigateByUrl('/cajero/reservas-pendientes');
  }

  onNuevaVentaDesdeModal(): void {
    this.modalPagoAbierto.set(false);
    this.paso.set('armando');
    this.lineas.set([]);
    this.ventaCreada.set(null);
    this.resultados.set([]);
    this.termino.set('');
    this.seBusco.set(false);
  }

  private _incrementarPorId(varianteId: number): void {
    const linea = this.lineas().find((l) => l.producto_variante_id === varianteId);
    if (!linea) {
      return;
    }
    if (linea.cantidad >= linea.disponible) {
      this.toast.error('No hay más disponibilidad para esa prenda.');
      return;
    }
    this.lineas.update((lineas) =>
      lineas.map((l) => (l.producto_variante_id === varianteId ? { ...l, cantidad: l.cantidad + 1 } : l)),
    );
  }
}
