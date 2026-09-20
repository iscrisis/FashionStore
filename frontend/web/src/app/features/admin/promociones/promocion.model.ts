// Modelo de CU32 -- Gestionar promociones (Administrador). Refleja 1:1 la
// forma que devuelve el backend (ver
// P6_InnovacionYAnalisis/CU32_GestionarPromociones/schemas.py) -- JSON
// puro, preparado para que Flutter lo consuma igual más adelante (aunque la
// gestión en sí sea exclusiva del panel web del Administrador).
//
// `estado` SIEMPRE viene ya calculado por FastAPI -- este modelo nunca lo
// deriva en Angular (ver service.py:_calcular_estado).

export type EstadoPromocion = 'PROGRAMADA' | 'ACTIVA' | 'FINALIZADA' | 'DESACTIVADA';

export interface ProductoPromocion {
  id: number;
  nombre: string;
  imagen_principal_url: string | null;
}

export interface PromocionListado {
  id: number;
  nombre: string;
  porcentaje_descuento: number;
  fecha_inicio: string;
  fecha_fin: string;
  estado: EstadoPromocion;
  cantidad_productos: number;
  fecha_creacion: string;
}

export interface PromocionDetalle {
  id: number;
  nombre: string;
  porcentaje_descuento: number;
  fecha_inicio: string;
  fecha_fin: string;
  estado: EstadoPromocion;
  activa: boolean;
  fecha_creacion: string;
  productos: ProductoPromocion[];
}

export interface PromocionPayload {
  nombre: string;
  porcentaje_descuento: number;
  fecha_inicio: string;
  fecha_fin: string;
  producto_ids: number[];
}
