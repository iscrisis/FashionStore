import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { Icon } from '../../../core/ui/icon/icon';
import { CancelarReserva } from '../cancelar-reserva/cancelar-reserva';
import { EstadoReserva, ReservaDetalleOut, ReservaOut } from '../crear-reserva/crear-reserva.model';
import { etiquetaEstadoReserva } from '../estado-reserva';
import { formatearFechaReserva, formatearHorarioReserva } from '../reserva-formato';
import { MisReservasService } from './mis-reservas.service';

// Tabs de CU18 -- una reserva vive en una sola pestaña a la vez, nunca
// mezcladas: Pendientes es la que abre por defecto (no hay pestaña "Todas",
// a propósito -- ver requerimiento). El orden de este arreglo es también el
// orden visual de las pestañas.
//
// Cada tab agrupa varios `estado` (CU20 -- Atender reserva de prendas amplió
// el ciclo de vida más allá de PENDIENTE/ATENDIDA/CANCELADA): "Pendientes"
// significa "todavía en curso, el Cliente puede necesitar hacer algo o solo
// esperar" (PENDIENTE/PREPARADA/EN_ATENCION/LISTA_PARA_CAJA); VENCIDA se
// agrupa junto a CANCELADA en "Canceladas" -- ambas son reservas que no
// terminaron en una atención real, pero el texto de cada tarjeta (ver
// estado-reserva.ts) las distingue con claridad ("Vencida" vs "Cancelada").
type TabKey = 'pendientes' | 'atendidas' | 'canceladas';

interface TabReserva {
  key: TabKey;
  etiqueta: string;
  estados: EstadoReserva[];
  vacio: string;
}

const TABS: TabReserva[] = [
  {
    key: 'pendientes',
    etiqueta: 'Pendientes',
    estados: ['PENDIENTE', 'PREPARADA', 'EN_ATENCION', 'LISTA_PARA_CAJA'],
    vacio: 'No tienes reservas pendientes.',
  },
  {
    key: 'atendidas',
    etiqueta: 'Atendidas',
    estados: ['ATENDIDA'],
    vacio: 'No tienes reservas atendidas.',
  },
  {
    key: 'canceladas',
    etiqueta: 'Canceladas',
    estados: ['CANCELADA', 'VENCIDA'],
    vacio: 'No tienes reservas canceladas.',
  },
];

/**
 * CU18 -- Consultar reserva (Cliente).
 *
 * Vive dentro del layout público (mismo navbar de FashionStore, ver
 * app.routes.ts: '/mis-reservas' es hijo del PublicLayout) -- no es un
 * dashboard nuevo, es una sección más de la cuenta del Cliente, igual que
 * '/mi-perfil' (CU04).
 *
 * Muestra tarjetas, no una tabla administrativa: cada una trae solo lo que
 * el Cliente necesita reconocer su reserva (imagen, producto, color, talla,
 * sucursal+ciudad, fecha, horario y estado en lenguaje llano) -- nunca ids
 * ni enums crudos. El backend ya resuelve el cliente desde el token (ver
 * CU17_CrearReservaPrendas/router.py) -- este componente nunca envía ni
 * decide de quién son las reservas que pide.
 */
@Component({
  selector: 'app-mis-reservas',
  imports: [Icon, CancelarReserva],
  templateUrl: './mis-reservas.html',
  styleUrl: './mis-reservas.scss',
})
export class MisReservas implements OnInit {
  private readonly service = inject(MisReservasService);

  protected readonly cargando = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly reservas = signal<ReservaOut[]>([]);

  protected readonly resolveMediaUrl = resolveMediaUrl;
  protected readonly etiquetaEstadoReserva = etiquetaEstadoReserva;

  protected readonly tabs = TABS;
  protected readonly tabActiva = signal<TabKey>('pendientes');

  // Filtra en Angular sobre la MISMA respuesta de GET /reservas/mias (CU17/18)
  // -- no hay endpoint nuevo ni parámetro de filtro: el volumen por Cliente
  // es chico y el backend ya trae todo lo necesario en una sola llamada.
  // Filtra por `estado_general` (agregado de TODOS los detalles, ver
  // Models/reserva.py:calcular_estado_general en el backend) -- una reserva
  // con prendas en distinto estado vive en una sola pestaña a la vez, igual
  // que antes de agrupar por reserva.
  protected readonly reservasFiltradas = computed(() => {
    const estados = this.tabs.find((tab) => tab.key === this.tabActiva())?.estados ?? [];
    return this.reservas().filter((reserva) => estados.includes(reserva.estado_general));
  });

  protected get mensajeVacio(): string {
    return this.tabs.find((tab) => tab.key === this.tabActiva())?.vacio ?? '';
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.errorMessage.set(null);
    this.service.listarMias().subscribe({
      next: (reservas) => {
        this.reservas.set(reservas);
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        this.errorMessage.set('No se pudieron cargar tus reservas. Inténtalo nuevamente.');
      },
    });
  }

  protected horario(reserva: ReservaOut): string {
    return formatearHorarioReserva(reserva.hora_inicio, reserva.hora_fin);
  }

  protected fecha(reserva: ReservaOut): string {
    return formatearFechaReserva(reserva.fecha_reserva);
  }

  seleccionarTab(key: TabKey): void {
    this.tabActiva.set(key);
  }

  // CU19 -- Cancelar reserva: reemplaza SOLO ese detalle (esa prenda) dentro
  // de su reserva en el arreglo local -- feedback instantáneo, sin esperar
  // ninguna respuesta nueva (ver CancelarReserva.confirmar(), que emite el
  // detalle ya actualizado, con estado CANCELADA). El resto de la reserva
  // (y de sus otras prendas) queda intacto en la UI.
  //
  // `estado_general` de la cabecera (usado para decidir en qué pestaña vive
  // la tarjeta, ver reservasFiltradas) es un AGREGADO que solo el backend
  // sabe recalcular (Models/reserva.py:calcular_estado_general) -- por eso,
  // además del parche local, se refresca la lista en silencio (sin mostrar
  // el skeleton de `cargando`) para que la tarjeta caiga en la pestaña
  // correcta si ese cambio hizo que toda la reserva pasara, por ejemplo, de
  // "Pendientes" a "Canceladas".
  protected onDetalleCancelado(reservaId: number, detalleActualizado: ReservaDetalleOut): void {
    this.reservas.update((lista) =>
      lista.map((reserva) =>
        reserva.id !== reservaId
          ? reserva
          : {
              ...reserva,
              detalles: reserva.detalles.map((detalle) =>
                detalle.id === detalleActualizado.id ? detalleActualizado : detalle,
              ),
            },
      ),
    );
    this.service.listarMias().subscribe({
      next: (reservas) => this.reservas.set(reservas),
      error: () => undefined, // el parche local ya quedó aplicado -- un refresco fallido no es crítico.
    });
  }
}
