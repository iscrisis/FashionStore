import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { FiltroHistorial } from '../../historial-compras/filtro-historial/filtro-historial';
import {
  FiltroHistorial as FiltroHistorialQuery,
  MetodoPagoHistorial,
  VentaHistorialOut,
} from '../../historial-compras/historial-compras.model';
import { HistorialComprasService } from '../../historial-compras/historial-compras.service';

/**
 * CU27 -- Consultar historial de compras (Cliente, "Mis compras").
 * Vive dentro del layout público ('/mis-compras', mismo navbar que
 * '/mi-perfil' y '/mis-reservas' -- ver app.routes.ts), no es un dashboard
 * nuevo. El backend ya resuelve `cliente_id` SIEMPRE del token (ver
 * CU27_ConsultarHistorialCompras/service.py) -- este componente nunca
 * decide ni envía de quién son las compras.
 *
 * "Ver" navega directo a la pantalla de comprobante ya construida por CU31
 * ('/comprobante/:ventaId', mismo detalle -- productos, color, talla,
 * cantidad, precio, subtotal, total, sucursal, fecha, método de pago -- y
 * el botón "Descargar") -- CU27 nunca reconstruye esa vista ni esa lógica
 * (requerimiento explícito: "no duplicar lógica de comprobantes").
 */
@Component({
  selector: 'app-historial-compras-cliente',
  imports: [RouterLink, Icon, FiltroHistorial],
  templateUrl: './historial-compras.html',
  styleUrl: './historial-compras.scss',
})
export class HistorialComprasCliente implements OnInit {
  private readonly service = inject(HistorialComprasService);

  protected readonly cargando = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly compras = signal<VentaHistorialOut[]>([]);

  ngOnInit(): void {
    this.cargar({});
  }

  cargar(filtro: FiltroHistorialQuery): void {
    this.cargando.set(true);
    this.errorMessage.set(null);
    this.service.listarMias(filtro).subscribe({
      next: (compras) => {
        this.cargando.set(false);
        this.compras.set(compras);
      },
      error: (err) => {
        this.cargando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.errorMessage.set(detalle ?? 'No se pudieron cargar tus compras. Inténtalo nuevamente.');
      },
    });
  }

  protected fecha(iso: string): string {
    const fecha = new Date(iso);
    const dd = String(fecha.getDate()).padStart(2, '0');
    const mm = String(fecha.getMonth() + 1).padStart(2, '0');
    return `${dd}/${mm}/${fecha.getFullYear()}`;
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
