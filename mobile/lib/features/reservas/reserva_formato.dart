/// Formato de fecha/horario de una reserva -- mismo criterio que
/// frontend/web/src/app/features/reservas/reserva-formato.ts.
library;

String formatearFechaReserva(String fechaIso) {
  final partes = fechaIso.split('-');
  return '${partes[2]}/${partes[1]}/${partes[0]}';
}

String formatearHorarioReserva(String horaInicio, String horaFin) {
  return '${horaInicio.substring(0, 5)} - ${horaFin.substring(0, 5)}';
}
