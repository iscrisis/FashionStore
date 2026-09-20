import { EstadoReserva } from './crear-reserva/crear-reserva.model';

// Traducción visual de CU18 (Mis reservas): el backend siempre expone el
// enum real (ver CU17 schemas.py) -- el texto amigable para el Cliente es
// puramente de presentación y vive solo aquí, en el frontend. Ampliado por
// CU20 (Atender reserva de prendas) con los estados que agrega el flujo del
// Encargado -- ver backend Models/reserva.py.
const ETIQUETAS_ESTADO_RESERVA: Record<EstadoReserva, string> = {
  PENDIENTE: 'Pendiente de preparación',
  PREPARADA: 'Lista para tu visita',
  EN_ATENCION: 'En atención',
  LISTA_PARA_CAJA: 'En proceso en sucursal',
  ATENDIDA: 'Atendida',
  CANCELADA: 'Cancelada',
  VENCIDA: 'Vencida',
};

export function etiquetaEstadoReserva(estado: EstadoReserva): string {
  return ETIQUETAS_ESTADO_RESERVA[estado];
}
