import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { Icon } from '../../../core/ui/icon/icon';
import { ToastService } from '../../../core/ui/toast/toast.service';
import { formatearFechaReserva, formatearHorarioReserva } from '../../reservas/reserva-formato';
import { AtenderReserva } from './atender-reserva/atender-reserva';
import { EstadoReservaPanel, ReservaDetallePanel, ReservaPanel } from './reservas.model';
import { PanelReservasService } from './reservas.service';

// Traducción visual para el Encargado -- copia propia (no la de CU18/
// estado-reserva.ts): esas etiquetas están escritas para el Cliente ("Lista
// para TU visita"), un panel interno no debe hablarle al Encargado en
// segunda persona como si fuera el propio Cliente.
const ETIQUETAS_ESTADO: Record<EstadoReservaPanel, string> = {
  PENDIENTE: 'Pendiente',
  PREPARADA: 'Preparada',
  EN_ATENCION: 'En atención',
  LISTA_PARA_CAJA: 'Lista para caja',
  ATENDIDA: 'Atendida',
  CANCELADA: 'Cancelada',
  VENCIDA: 'Vencida',
};

// Grupos del panel -- "como mínimo" los 3 que pide el requerimiento.
// LISTA_PARA_CAJA se agrupa en "Finalizadas": una vez que el Encargado
// finalizó la atención, ya no hay ninguna acción más de CU20 sobre ella.
type GrupoKey = 'pendientes' | 'en_atencion' | 'finalizadas';

interface GrupoReserva {
  key: GrupoKey;
  etiqueta: string;
  estados: EstadoReservaPanel[];
  vacio: string;
}

const GRUPOS: GrupoReserva[] = [
  {
    key: 'pendientes',
    etiqueta: 'Pendientes',
    estados: ['PENDIENTE', 'PREPARADA'],
    vacio: 'No hay reservas pendientes.',
  },
  {
    key: 'en_atencion',
    etiqueta: 'En atención',
    estados: ['EN_ATENCION'],
    vacio: 'No hay reservas en atención.',
  },
  {
    key: 'finalizadas',
    etiqueta: 'Finalizadas',
    estados: ['ATENDIDA', 'LISTA_PARA_CAJA', 'CANCELADA', 'VENCIDA'],
    vacio: 'No hay reservas finalizadas.',
  },
];

// Un detalle sin decisión todavía -- bloquea "Finalizar atención" de toda
// la reserva (ver puedeFinalizarAtencion).
const ESTADOS_SIN_DECISION: EstadoReservaPanel[] = ['PENDIENTE', 'PREPARADA'];

/**
 * CU20 -- Atender reserva de prendas (Encargado de Sucursal).
 *
 * Panel propio del Encargado (layout /encargado, ver app.routes.ts) --
 * separado de "Mis reservas" del Cliente (CU18, layout público). El backend
 * resuelve SIEMPRE la sucursal desde el token: este componente nunca envía
 * ni decide de qué sucursal son las reservas que pide.
 *
 * Tarjetas agrupadas en Pendientes / En atención / Finalizadas -- nunca una
 * tabla administrativa pesada. Una tarjeta = una RESERVA (cabecera: código,
 * cliente, fecha/horario, estado agregado), con todas sus prendas anidadas
 * en `detalles`. Dos niveles de acción, nunca mezclados:
 *   - a nivel RESERVA (este componente): "Confirmar llegada" (PENDIENTE|
 *     PREPARADA -> EN_ATENCION, sin modal -- paso de bajo riesgo) y
 *     "Finalizar atención" (EN_ATENCION -> LISTA_PARA_CAJA|ATENDIDA, detrás
 *     de un modal de confirmación con el resumen de decisiones -- libera
 *     stock de las prendas no compradas, así que sí lo amerita). Un solo
 *     botón de cada uno por tarjeta, nunca repetido por prenda.
 *   - a nivel DETALLE (AtenderReserva, ver atender-reserva.ts): preparar
 *     y decidir no comprar/enviar a caja, una instancia por prenda.
 */
@Component({
  selector: 'app-reservas-encargado',
  imports: [Icon, AtenderReserva],
  templateUrl: './reservas.html',
  styleUrl: './reservas.scss',
})
export class Reservas implements OnInit {
  private readonly service = inject(PanelReservasService);
  private readonly toast = inject(ToastService);

  protected readonly cargando = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly reservas = signal<ReservaPanel[]>([]);

  protected readonly resolveMediaUrl = resolveMediaUrl;
  protected readonly etiquetaEstado = (estado: EstadoReservaPanel) => ETIQUETAS_ESTADO[estado];

  protected readonly grupos = GRUPOS;
  protected readonly grupoActivo = signal<GrupoKey>('pendientes');

  // Filtra en Angular sobre la MISMA respuesta de GET /reservas/panel -- sin
  // endpoint ni parámetro de filtro nuevos, mismo criterio ya usado por CU18
  // (mis-reservas.ts) para sus propias pestañas. Filtra por `estado_general`
  // (ver backend Models/reserva.py).
  protected readonly reservasFiltradas = computed(() => {
    const estados = this.grupos.find((g) => g.key === this.grupoActivo())?.estados ?? [];
    return this.reservas().filter((reserva) => estados.includes(reserva.estado_general));
  });

  protected get mensajeVacio(): string {
    return this.grupos.find((g) => g.key === this.grupoActivo())?.vacio ?? '';
  }

  // "Confirmar llegada" -- id de la reserva en curso, para deshabilitar solo
  // ese botón mientras se procesa (doble clic).
  protected readonly confirmandoLlegadaId = signal<number | null>(null);

  // Modal "Finalizar atención" -- reserva sobre la que está abierto (o null,
  // cerrado) y su propio estado de envío.
  protected readonly reservaAFinalizar = signal<ReservaPanel | null>(null);
  protected readonly finalizando = signal(false);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.errorMessage.set(null);
    this.service.listarPanel().subscribe({
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

  seleccionarGrupo(key: GrupoKey): void {
    this.grupoActivo.set(key);
  }

  protected detallesParaCaja(reserva: ReservaPanel): ReservaDetallePanel[] {
    return reserva.detalles.filter((d) => d.estado === 'LISTA_PARA_CAJA');
  }

  protected detallesNoCompra(reserva: ReservaPanel): ReservaDetallePanel[] {
    return reserva.detalles.filter((d) => d.estado === 'ATENDIDA');
  }

  protected puedeFinalizarAtencion(reserva: ReservaPanel): boolean {
    return (
      reserva.estado_general === 'EN_ATENCION' &&
      !reserva.detalles.some((d) => ESTADOS_SIN_DECISION.includes(d.estado))
    );
  }

  // "Confirmar llegada" -- un solo botón por reserva, sin modal (paso de
  // bajo riesgo: no toca stock ni el estado de ninguna prenda).
  confirmarLlegada(reserva: ReservaPanel): void {
    if (this.confirmandoLlegadaId() !== null) {
      return;
    }
    this.confirmandoLlegadaId.set(reserva.id);
    this.service.confirmarLlegada(reserva.id).subscribe({
      next: (actualizada) => {
        this.confirmandoLlegadaId.set(null);
        this.toast.brand('Llegada del cliente confirmada.');
        this.onReservaActualizada(actualizada);
      },
      error: (err) => {
        this.confirmandoLlegadaId.set(null);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo confirmar la llegada. Inténtalo nuevamente.');
      },
    });
  }

  abrirModalFinalizar(reserva: ReservaPanel): void {
    if (!this.puedeFinalizarAtencion(reserva)) {
      return;
    }
    this.reservaAFinalizar.set(reserva);
  }

  cerrarModalFinalizar(): void {
    if (this.finalizando()) {
      return;
    }
    this.reservaAFinalizar.set(null);
  }

  confirmarFinalizarAtencion(): void {
    const reserva = this.reservaAFinalizar();
    if (!reserva || this.finalizando()) {
      return;
    }
    this.finalizando.set(true);
    this.service.finalizarAtencion(reserva.id).subscribe({
      next: (actualizada) => {
        this.finalizando.set(false);
        this.reservaAFinalizar.set(null);
        this.toast.brand('Atención finalizada.');
        this.onReservaActualizada(actualizada);
      },
      error: (err) => {
        this.finalizando.set(false);
        const detalle = typeof err?.error?.detail === 'string' ? err.error.detail : null;
        this.toast.error(detalle ?? 'No se pudo finalizar la atención. Inténtalo nuevamente.');
      },
    });
  }

  // Reemplaza la CABECERA completa en el arreglo local -- usado por
  // confirmar llegada / finalizar atención, que devuelven la reserva
  // entera (a diferencia de las acciones por detalle).
  private onReservaActualizada(actualizada: ReservaPanel): void {
    this.reservas.update((lista) => lista.map((r) => (r.id === actualizada.id ? actualizada : r)));
  }

  // Reemplaza SOLO ese detalle (esa prenda) dentro de su reserva en el
  // arreglo local -- feedback instantáneo (ver AtenderReserva, que emite el
  // detalle ya actualizado). Ninguna acción por detalle cambia
  // estado_general (ver backend service.py), así que no hace falta
  // refrescar el panel completo.
  protected onDetalleActualizado(reservaId: number, detalleActualizado: ReservaDetallePanel): void {
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
  }
}
