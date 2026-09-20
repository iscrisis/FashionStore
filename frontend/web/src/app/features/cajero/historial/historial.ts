import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FiltroHistorial } from '../../historial-compras/filtro-historial/filtro-historial';
import {
  FiltroHistorial as FiltroHistorialQuery,
  MetodoPagoHistorial,
  VentaHistorialOut,
} from '../../historial-compras/historial-compras.model';
import { HistorialComprasService } from '../../historial-compras/historial-compras.service';

// Pestañas de CU27 (Cajero) -- SOLO consulta, filtran en Angular sobre la
// MISMA respuesta de GET /historial-compras/sucursal (mismo criterio que
// CU18/mis-reservas.ts con sus tabs): "Pagadas" = sin ninguna operación de
// CU26 registrada; "Postventa" = con al menos una; "Todas" = sin filtrar.
// No hay endpoint ni estado de Venta por pestaña -- `tiene_postventa` ya
// viene calculado por el backend (ver historial-compras.model.ts).
type TabKey = 'pagadas' | 'postventa' | 'todas';

interface TabHistorial {
  key: TabKey;
  etiqueta: string;
  vacio: string;
}

const TABS: TabHistorial[] = [
  { key: 'pagadas', etiqueta: 'Pagadas', vacio: 'No hay ventas pagadas sin devoluciones o cambios.' },
  { key: 'postventa', etiqueta: 'Postventa', vacio: 'No hay ventas con devoluciones o cambios registrados.' },
  { key: 'todas', etiqueta: 'Todas', vacio: 'No se encontraron ventas.' },
];

/**
 * CU27 -- Consultar historial de compras (Cajero). Vive bajo CajeroLayout
 * ('/cajero/historial', ítem propio "Historial" del sidebar -- ver
 * layouts/cajero-layout/cajero-sidebar). Lista TODAS las ventas PAGADAS de
 * SU sucursal (resuelta siempre del token en el backend, nunca de esta
 * pantalla) -- sin importar qué Cajero las vendió: sirve para atención
 * posterior y devoluciones, no solo para "mis propias ventas".
 *
 * SOLO consulta -- a propósito, ya NO ofrece "Devolución"/"Cambiar": esas
 * acciones viven exclusivamente en CU26 ("Devoluciones y cambios", propio
 * ítem del sidebar, con su flujo "buscar VT-XXXXX -> Devolver/Cambiar").
 * "Ver" es la ÚNICA acción visible por fila -- reutiliza CU31 tal cual,
 * navegando a la pantalla de comprobante del Cajero ya construida
 * ('/cajero/comprobante/:ventaId', que ya ofrece Descargar/Enviar) -- la
 * lista en sí ya no descarga nada directamente (ajuste visual: la fila se
 * mantiene liviana, sin una segunda acción de comprobante).
 */
@Component({
  selector: 'app-historial-cajero',
  imports: [RouterLink, FiltroHistorial],
  templateUrl: './historial.html',
  styleUrl: './historial.scss',
})
export class Historial implements OnInit {
  private readonly service = inject(HistorialComprasService);

  protected readonly cargando = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly ventas = signal<VentaHistorialOut[]>([]);

  protected readonly tabs = TABS;
  protected readonly tabActiva = signal<TabKey>('pagadas');

  protected readonly ventasFiltradas = computed(() => {
    const tab = this.tabActiva();
    const ventas = this.ventas();
    if (tab === 'pagadas') {
      return ventas.filter((venta) => !venta.tiene_postventa);
    }
    if (tab === 'postventa') {
      return ventas.filter((venta) => venta.tiene_postventa);
    }
    return ventas;
  });

  protected get mensajeVacio(): string {
    return this.tabs.find((tab) => tab.key === this.tabActiva())?.vacio ?? '';
  }

  ngOnInit(): void {
    this.cargar({});
  }

  seleccionarTab(key: TabKey): void {
    this.tabActiva.set(key);
  }

  cargar(filtro: FiltroHistorialQuery): void {
    this.cargando.set(true);
    this.errorMessage.set(null);
    this.service.listarSucursal(filtro).subscribe({
      next: (ventas) => {
        this.cargando.set(false);
        this.ventas.set(ventas);
      },
      error: (err) => {
        this.cargando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.errorMessage.set(detalle ?? 'No se pudo cargar el historial. Inténtalo nuevamente.');
      },
    });
  }

  protected fecha(iso: string): string {
    const fecha = new Date(iso);
    const dd = String(fecha.getDate()).padStart(2, '0');
    const mm = String(fecha.getMonth() + 1).padStart(2, '0');
    const hh = String(fecha.getHours()).padStart(2, '0');
    const min = String(fecha.getMinutes()).padStart(2, '0');
    return `${dd}/${mm}/${fecha.getFullYear()} ${hh}:${min}`;
  }

  protected etiquetaTipo(tipo: string): string {
    return tipo === 'DIGITAL' ? 'Digital' : 'Presencial';
  }

  protected etiquetaMetodo(metodo: MetodoPagoHistorial): string {
    const etiquetas: Record<MetodoPagoHistorial, string> = {
      STRIPE: 'Stripe',
      EFECTIVO: 'Efectivo',
      TARJETA: 'Tarjeta',
      QR: 'QR',
    };
    return etiquetas[metodo] ?? metodo;
  }
}
