// Formato de fecha/horario de una reserva -- compartido entre CU18 (Mis
// reservas) y CU19 (Cancelar reserva, que muestra el mismo resumen dentro
// del modal de confirmación) para no duplicar el mismo mapeo dos veces.

export function formatearFechaReserva(fechaIso: string): string {
  const [anio, mes, dia] = fechaIso.split('-');
  return `${dia}/${mes}/${anio}`;
}

export function formatearHorarioReserva(horaInicio: string, horaFin: string): string {
  return `${horaInicio.slice(0, 5)} - ${horaFin.slice(0, 5)}`;
}
