// Reglas de fecha/horario de CU17 -- Crear reserva de prendas.
//
// Mismas constantes que backend/.../CU17_CrearReservaPrendas/service.py
// (DIAS_MAXIMO_ANTICIPACION, HORA_APERTURA, HORA_CIERRE_LUN_A_SAB,
// DOMINGO_WEEKDAY): Angular las usa SOLO para armar el tarjetero de
// fecha/hora del modal (deshabilitar opciones inválidas antes de
// enviarlas) -- la autoridad real es siempre el backend, que vuelve a
// validar todo en el POST /reservas (ver
// CrearReservaService._validar_fecha_hora). Cuando exista la app Flutter,
// debe replicar exactamente estos mismos valores para ofrecer la misma
// experiencia, ya que ambos clientes hablan con el mismo backend REST.
//
// "Ahora" se calcula en UTC (Date.getUTC*), NO con la hora local del
// navegador: el backend compara fecha_reserva/hora_inicio contra
// datetime.now(timezone.utc) tal cual llegan, sin convertir zona horaria
// (mismo criterio que ya usa todo el proyecto, ver CU03 RecuperarContrasena
// -- no existe hoy una noción de "huso horario de la tienda"). Si Angular
// calculara "hoy"/"ahora" con la hora local del visitante, un slot podría
// verse disponible en la interfaz y el backend rechazarlo igual (o al
// revés), porque estarían comparando contra relojes distintos.

export const DIAS_MAXIMO_ANTICIPACION = 7;

export const HORA_APERTURA = '10:00';
export const HORA_CIERRE_LUN_A_SAB = '20:00';
export const DOMINGO_WEEKDAY = 0; // Date.getUTCDay(): domingo = 0

const MINUTOS_ANTICIPACION_MINIMA = 60;

function aMinutos(horaHHmm: string): number {
  const [h, m] = horaHHmm.split(':').map(Number);
  return h * 60 + m;
}

function aHoraHHmm(minutosDesdeMedianoche: number): string {
  const h = Math.floor(minutosDesdeMedianoche / 60);
  return `${String(h).padStart(2, '0')}:00`;
}

/** "YYYY-MM-DD" de una fecha, en UTC -- ver nota de cabecera sobre por qué
 * todo este archivo usa UTC en vez de la hora local del navegador. */
function fechaAIsoUtc(fecha: Date): string {
  const y = fecha.getUTCFullYear();
  const m = String(fecha.getUTCMonth() + 1).padStart(2, '0');
  const d = String(fecha.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function hoyIso(): string {
  return fechaAIsoUtc(new Date());
}

/** Última fecha reservable (hoy + 7 días, UTC), en "YYYY-MM-DD". */
export function fechaMaximaIso(): string {
  const limite = new Date();
  limite.setUTCDate(limite.getUTCDate() + DIAS_MAXIMO_ANTICIPACION);
  return fechaAIsoUtc(limite);
}

export function esDomingo(fechaIso: string): boolean {
  return new Date(`${fechaIso}T00:00:00Z`).getUTCDay() === DOMINGO_WEEKDAY;
}

/**
 * Bloques de 1h disponibles para una fecha ya elegida (formato "HH:00"). Un
 * domingo siempre devuelve [] (no hay atención). Para el resto de los días,
 * ya filtrados por horario de atención y, si la fecha es hoy (en UTC), por
 * la anticipación mínima de 1 hora respecto a la hora UTC actual.
 */
export function bloquesHorarioDisponibles(fechaIso: string): string[] {
  if (esDomingo(fechaIso)) {
    return [];
  }

  const apertura = aMinutos(HORA_APERTURA);
  const cierre = aMinutos(HORA_CIERRE_LUN_A_SAB);
  const ultimoBloque = cierre - 60;

  const bloques: number[] = [];
  for (let minutos = apertura; minutos <= ultimoBloque; minutos += 60) {
    bloques.push(minutos);
  }

  if (fechaIso === hoyIso()) {
    const ahora = new Date();
    const minutoActualUtc = ahora.getUTCHours() * 60 + ahora.getUTCMinutes();
    const minimoValido = minutoActualUtc + MINUTOS_ANTICIPACION_MINIMA;
    return bloques.filter((m) => m >= minimoValido).map(aHoraHHmm);
  }

  return bloques.map(aHoraHHmm);
}

export interface DiaSeleccionable {
  iso: string;
  etiqueta: string;
  esDomingo: boolean;
}

const ABREVIATURAS_DIA = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

/**
 * Los próximos DIAS_MAXIMO_ANTICIPACION + 1 días (hoy incluido), como
 * tarjetas para el modal de CU17 -- "Lun 16", "Mar 17", etc. Los domingos
 * quedan marcados (esDomingo) para deshabilitarlos en la plantilla, nunca
 * se omiten de la lista: el Cliente debe VER que ese día no atiende, no
 * encontrarse con un hueco sin explicación.
 */
export function proximosDias(): DiaSeleccionable[] {
  const dias: DiaSeleccionable[] = [];
  const base = new Date();
  for (let i = 0; i <= DIAS_MAXIMO_ANTICIPACION; i++) {
    const fecha = new Date(base);
    fecha.setUTCDate(fecha.getUTCDate() + i);
    const iso = fechaAIsoUtc(fecha);
    const diaSemana = fecha.getUTCDay();
    dias.push({
      iso,
      etiqueta: `${ABREVIATURAS_DIA[diaSemana]} ${fecha.getUTCDate()}`,
      esDomingo: diaSemana === DOMINGO_WEEKDAY,
    });
  }
  return dias;
}
