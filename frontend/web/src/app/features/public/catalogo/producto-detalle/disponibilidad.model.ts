// Modelo de disponibilidad por sucursal (CU12) -- solo lectura, sin
// autenticación. Cruza las variantes (talla+color) de un producto (CU08) con
// el stock real por sucursal (mismo dato que ya administra el Encargado, ver
// CU14_ConsultarInventario); no inventa "Disponible"/"Agotado" aquí, eso se
// deriva del componente a partir de `cantidad`.
//
// Refleja 1:1 la forma que devuelve el backend (ver schemas.py de CU12) para
// que Flutter pueda consumir la misma estructura sin lógica intermedia:
//
//   producto
//    └── disponibilidad
//          ├── sucursal
//          └── variantes (talla + color + cantidad)
//
// producto_variante_id se agregó para CU17 (crear reserva de prendas): el
// Cliente lo necesita para reservar una variante puntual, no solo mostrarla.

export interface VarianteDisponible {
  producto_variante_id: number;
  talla_id: number;
  talla: string;
  color_id: number;
  color: string;
  cantidad: number;
}

export interface DisponibilidadSucursal {
  sucursal_id: number;
  sucursal: string;
  ciudad_id: number;
  ciudad: string;
  variantes: VarianteDisponible[];
}

export interface ProductoDisponibilidad {
  producto_id: number;
  disponibilidad: DisponibilidadSucursal[];
}
