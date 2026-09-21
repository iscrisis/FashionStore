/// Reglas de fecha/horario de CU17 -- Crear reserva de prendas. Mismas
/// constantes que backend/modules/P4_ReservasYAtencion/
/// CU17_CrearReservaPrendas/service.py y frontend/web/.../crear-reserva/
/// horario-reserva.ts: Flutter las usa SOLO para armar el tarjetero de
/// fecha/hora (deshabilitar opciones inválidas antes de enviarlas) -- la
/// autoridad real es SIEMPRE el backend, que vuelve a validar todo en el
/// POST /reservas.
///
/// "Ahora" se calcula en UTC (`DateTime.now().toUtc()`), NO con la hora
/// local del dispositivo: el backend compara fecha_reserva/hora_inicio
/// contra `datetime.now(timezone.utc)` tal cual llegan, sin convertir zona
/// horaria (mismo criterio que ya usa Angular y el resto del proyecto).
library;

const int diasMaximoAnticipacion = 7;
const int horaAperturaHora = 10;
const int horaCierreLunASabHora = 20;
const int minutosAnticipacionMinima = 60;

String _dosDigitos(int valor) => valor.toString().padLeft(2, '0');

String _fechaAIso(DateTime fechaUtc) {
  return '${fechaUtc.year}-${_dosDigitos(fechaUtc.month)}-${_dosDigitos(fechaUtc.day)}';
}

String hoyIso() => _fechaAIso(DateTime.now().toUtc());

/// Última fecha reservable (hoy + 7 días, UTC), en "YYYY-MM-DD".
String fechaMaximaIso() {
  final limite = DateTime.now().toUtc().add(const Duration(days: diasMaximoAnticipacion));
  return _fechaAIso(limite);
}

bool esDomingo(String fechaIso) {
  return DateTime.parse('${fechaIso}T00:00:00Z').weekday == DateTime.sunday;
}

/// Bloques de 1h disponibles para una fecha ya elegida (formato "HH:00").
/// Un domingo siempre devuelve [] (no hay atención). Para el resto de los
/// días, ya filtrados por horario de atención y, si la fecha es hoy (UTC),
/// por la anticipación mínima de 1 hora respecto a la hora UTC actual.
List<String> bloquesHorarioDisponibles(String fechaIso) {
  if (esDomingo(fechaIso)) return [];

  final aperturaMin = horaAperturaHora * 60;
  final cierreMin = horaCierreLunASabHora * 60;
  final ultimoBloqueMin = cierreMin - 60;

  final bloques = <int>[for (var m = aperturaMin; m <= ultimoBloqueMin; m += 60) m];

  if (fechaIso == hoyIso()) {
    final ahora = DateTime.now().toUtc();
    final minutoActual = ahora.hour * 60 + ahora.minute;
    final minimoValido = minutoActual + minutosAnticipacionMinima;
    return bloques.where((m) => m >= minimoValido).map((m) => '${_dosDigitos(m ~/ 60)}:00').toList();
  }

  return bloques.map((m) => '${_dosDigitos(m ~/ 60)}:00').toList();
}

class DiaSeleccionable {
  const DiaSeleccionable({required this.iso, required this.etiqueta, required this.esDomingo});

  final String iso;
  final String etiqueta;
  final bool esDomingo;
}

const List<String> _abreviaturasDia = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

/// Los próximos `diasMaximoAnticipacion` + 1 días (hoy incluido), como
/// tarjetas para el modal de CU17. Los domingos quedan marcados
/// (`esDomingo`) para deshabilitarlos en la UI, nunca se omiten de la
/// lista: el Cliente debe VER que ese día no atiende, no encontrarse con un
/// hueco sin explicación.
List<DiaSeleccionable> proximosDias() {
  final hoyUtc = DateTime.now().toUtc();
  final base = DateTime.utc(hoyUtc.year, hoyUtc.month, hoyUtc.day);
  return [
    for (var i = 0; i <= diasMaximoAnticipacion; i++)
      _diaSeleccionableDe(base.add(Duration(days: i))),
  ];
}

DiaSeleccionable _diaSeleccionableDe(DateTime fechaUtc) {
  // DateTime.weekday: lunes=1 ... domingo=7 -- % 7 lo alinea con
  // _abreviaturasDia (domingo=0), igual que Date.getUTCDay() en Angular.
  final diaSemana = fechaUtc.weekday % 7;
  return DiaSeleccionable(
    iso: _fechaAIso(fechaUtc),
    etiqueta: '${_abreviaturasDia[diaSemana]} ${fechaUtc.day}',
    esDomingo: fechaUtc.weekday == DateTime.sunday,
  );
}
