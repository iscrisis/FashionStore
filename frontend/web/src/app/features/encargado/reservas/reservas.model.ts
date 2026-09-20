// Modelo de CU20 -- Atender reserva de prendas (panel del Encargado). Refleja
// 1:1 la forma que devuelve el backend (ver CU20_AtenderReservaPrendas/schemas.py)
// -- JSON puro, preparado para que Flutter lo consuma igual más adelante,
// aunque este panel es exclusivamente Angular Web por ahora.
//
// `ReservaPanel` es la cabecera (una tarjeta = una reserva = una visita del
// Cliente) con TODAS sus prendas anidadas en `detalles`. Dos niveles de
// acción, NUNCA mezclados (ver backend service.py):
//   - a nivel RESERVA (confirmar llegada, finalizar atención): un solo botón
//     por reserva, cambia `estado_general` -- nunca el `estado` de un
//     detalle individual.
//   - a nivel DETALLE (preparar, decidir no comprar / enviar a caja): un
//     `ReservaDetallePanel` por prenda, nunca afecta a las demás ni a la
//     cabecera directamente.
//
// Distinto del modelo de CU17/CU18 (crear-reserva.model.ts): el Encargado
// necesita `cliente` (quién reservó) y nunca `sucursal` (siempre es la suya
// propia, resuelta por el backend desde el token).

export type EstadoReservaPanel =
  | 'PENDIENTE'
  | 'PREPARADA'
  | 'EN_ATENCION'
  | 'LISTA_PARA_CAJA'
  | 'CANCELADA'
  | 'ATENDIDA'
  | 'VENCIDA';

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

export interface ClienteResumen {
  id: number;
  nombre: string;
}

export interface ReservaDetallePanel {
  id: number;
  reserva_id: number;
  producto: ProductoResumen;
  variante: VarianteResumen;
  cantidad: number;
  estado: EstadoReservaPanel;
}

export interface ReservaPanel {
  id: number;
  codigo_reserva: string;
  cliente: ClienteResumen;
  estado_general: EstadoReservaPanel;
  fecha_reserva: string;
  hora_inicio: string;
  hora_fin: string;
  fecha_creacion: string;
  detalles: ReservaDetallePanel[];
}
