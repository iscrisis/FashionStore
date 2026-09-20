import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { formatearFechaReserva, formatearHorarioReserva } from '../../reservas/reserva-formato';
import { ReservaPanel } from '../../encargado/reservas/reservas.model';
import { ProcesarPago } from '../ventas/procesar-pago/procesar-pago';
import { VentaPresencialOut } from '../ventas/venta-presencial.model';
import { VentaPresencialService } from '../ventas/venta-presencial.service';
import { ReservasPendientesService } from './reservas-pendientes.service';

/**
 * Integración mínima de CU20 con el rol Cajero -- "Reservas pendientes de
 * atención".
 *
 * Vive bajo CajeroLayout ('/cajero/reservas-pendientes', "Reservas para
 * caja" del sidebar -- ver layouts/cajero-layout) -- este componente ya NO
 * trae su propia barra superior ni "Cerrar sesión": ambos los da el layout.
 * Muestra únicamente las reservas cuyo estado_general el Encargado (CU20) ya
 * dejó en LISTA_PARA_CAJA para SU sucursal (resuelta siempre del token en el
 * backend, nunca de esta pantalla) -- agrupadas (una tarjeta por reserva,
 * con sus prendas para caja anidadas, igual que el panel del Encargado).
 *
 * CU24 agrega "+ Nueva venta" (arriba de la lista) -> navega a
 * /cajero/ventas/nueva, venta DIRECTA (sin reserva); sin lógica propia aquí.
 *
 * CU25 agrega "Cargar venta" en cada tarjeta LISTA_PARA_CAJA -- YA NO
 * navega a otra página: crea/reutiliza la Venta (CU24,
 * `crearVentaDesdeReserva`) y abre <app-procesar-pago> como ficha flotante
 * sobre esta misma pantalla (fondo oscurecido) -- el ÚNICO componente de
 * pago, el mismo que usa "Continuar al pago" en venta-directa.ts, nunca
 * duplicado. Botón propio de la tarjeta, nunca toda la tarjeta clicable
 * (evita un clic ambiguo) -- el resto sigue siendo de solo lectura. Al
 * confirmar el pago, esa reserva pasa a ATENDIDA en el backend -- por eso
 * la lista se refresca (`cargar()`), para que deje de aparecer aquí.
 */
@Component({
  selector: 'app-reservas-pendientes-cajero',
  imports: [Icon, RouterLink, ProcesarPago],
  templateUrl: './reservas-pendientes.html',
  styleUrl: './reservas-pendientes.scss',
})
export class ReservasPendientes implements OnInit {
  private readonly service = inject(ReservasPendientesService);
  private readonly ventaPresencialService = inject(VentaPresencialService);
  private readonly router = inject(Router);

  protected readonly cargando = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly reservas = signal<ReservaPanel[]>([]);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly cargandoVenta = signal<number | null>(null);
  protected readonly ventaParaPago = signal<VentaPresencialOut | null>(null);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.errorMessage.set(null);
    this.service.listarPendientes().subscribe({
      next: (reservas) => {
        this.reservas.set(reservas);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.errorMessage.set('No se pudieron cargar las reservas. Inténtalo nuevamente.');
      },
    });
  }

  protected fecha(reserva: ReservaPanel): string {
    return formatearFechaReserva(reserva.fecha_reserva);
  }

  protected horario(reserva: ReservaPanel): string {
    return formatearHorarioReserva(reserva.hora_inicio, reserva.hora_fin);
  }

  cargarVenta(reserva: ReservaPanel): void {
    if (this.cargandoVenta() !== null) {
      return;
    }
    this.cargandoVenta.set(reserva.id);
    this.ventaPresencialService.crearVentaDesdeReserva(reserva.id).subscribe({
      next: (venta) => {
        this.cargandoVenta.set(null);
        this.ventaParaPago.set(venta);
      },
      error: () => {
        this.cargandoVenta.set(null);
        this.errorMessage.set('No se pudo cargar la venta de esa reserva. Inténtalo nuevamente.');
      },
    });
  }

  cerrarModalPago(): void {
    // Sin pagar -- la Venta sigue PENDIENTE_PAGO, nada que refrescar.
    this.ventaParaPago.set(null);
  }

  onPagoRegistrado(): void {
    // La reserva ya pasó a ATENDIDA en el backend -- se refresca la lista
    // para que deje de aparecer como pendiente.
    this.ventaParaPago.set(null);
    this.cargar();
  }

  onNuevaVentaDesdeModal(): void {
    this.ventaParaPago.set(null);
    this.router.navigateByUrl('/cajero/ventas/nueva');
  }
}
