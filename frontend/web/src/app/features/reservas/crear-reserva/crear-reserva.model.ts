// Modelo de CU17 -- Crear reserva de prendas (Cliente). Refleja 1:1 la forma
// que expone el backend (ver schemas.py de CU17) para que Flutter pueda
// consumir la misma estructura más adelante.
//
// La reserva NO descuenta stock (ver Models/reserva.py en el backend): solo
// valida disponibilidad al crearse. sucursal_id lo elige el propio Cliente
// (a diferencia de CU16, donde la sucursal sale siempre de la cuenta del
// Encargado) -- por eso viaja en el request, no se deriva de la sesión.
//
// `ReservaOut` es la CABECERA de una reserva (una visita del Cliente a una
// sucursal, en un bloque horario) con sus prendas anidadas en `detalles` --
// nunca una fila por prenda. CU17 todavía no expone un carrito (el Cliente
// sigue reservando una prenda a la vez, ver crear-reserva.ts): arma una
// reserva con un único detalle, pero ya con esta forma agrupada, lista para
// cuando exista un carrito real (CU21, fuera de alcance).

// Agregado por CU20 (Atender reserva de prendas, panel del Encargado):
// PREPARADA, EN_ATENCION, LISTA_PARA_CAJA y VENCIDA amplían el ciclo de vida
// más allá de PENDIENTE/CANCELADA/ATENDIDA -- ver backend Models/reserva.py
// para el flujo completo.
export type EstadoReserva =
  | 'PENDIENTE'
  | 'PREPARADA'
  | 'EN_ATENCION'
  | 'LISTA_PARA_CAJA'
  | 'CANCELADA'
  | 'ATENDIDA'
  | 'VENCIDA';

export interface CrearReservaPayload {
  producto_variante_id: number;
  sucursal_id: number;
  cantidad: number;
  fecha_reserva: string;
  hora_inicio: string;
}

// Agregar una prenda a una reserva PENDIENTE ya existente (GET
// /reservas/compatibles + POST /reservas/{id}/detalles) -- no pide sucursal
// ni fecha/hora: esos datos son siempre los de la cabecera a la que se
// agrega. Ver CrearReservaService.agregar_detalle en el backend.
export interface AgregarDetallePayload {
  producto_variante_id: number;
  cantidad: number;
}

export interface TallaResumen {
  id: number;
  nombre: string;
}

export interface ColorResumen {
  id: number;
  nombre: string;
}

export interface VarianteResumen {
  id: number;
  talla: TallaResumen;
  color: ColorResumen;
}

export interface ProductoResumen {
  id: number;
  nombre: string;
  imagen_principal_url: string | null;
}

export interface CiudadResumen {
  id: number;
  nombre: string;
}

export interface SucursalResumen {
  id: number;
  nombre: string;
  // Agregado para CU18 (Mis reservas): la tarjeta muestra sucursal + ciudad.
  ciudad: CiudadResumen;
}

export interface ReservaDetalleOut {
  id: number;
  producto: ProductoResumen;
  variante: VarianteResumen;
  cantidad: number;
  estado: EstadoReserva;
}

export interface ReservaOut {
  id: number;
  // Identificador visible para el Cliente (ej. "RS-00025") -- se muestra
  // siempre en vez del `id` interno. Ver Models/reserva.py en el backend.
  codigo_reserva: string;
  sucursal: SucursalResumen;
  estado_general: EstadoReserva;
  fecha_reserva: string;
  hora_inicio: string;
  // Agregado para CU18 (Mis reservas): el bloque reservado siempre dura 1h
  // exacta -- el backend lo calcula a partir de hora_inicio (ver CU17 service.py).
  hora_fin: string;
  fecha_creacion: string;
  detalles: ReservaDetalleOut[];
}
