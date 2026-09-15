// Modelos exclusivos de CU16 -- Registrar movimientos de inventario. La
// sucursal NUNCA viaja en estos modelos: el backend siempre la resuelve del
// usuario autenticado (ver RegistrarMovimientoPayload más abajo), igual que
// ya hacen CU14 (panel-encargado.model.ts) y CU15 (recepcion-mercaderia.model.ts).
//
// Es un CU independiente de CU14 (consulta) y CU15 (recepción de
// proveedor): archivo propio en vez de extender los modelos de esos dos,
// mismo criterio que ya usó CU15 al no reutilizar panel-encargado.model.ts.

export type TipoMovimiento = 'AJUSTE_POSITIVO' | 'AJUSTE_NEGATIVO';

export interface TallaResumen {
  id: number;
  nombre: string;
}

export interface ColorResumen {
  id: number;
  nombre: string;
}

export interface VarianteConStock {
  id: number;
  talla: TallaResumen;
  color: ColorResumen;
  cantidad: number;
}

export interface ProductoConVariantes {
  id: number;
  nombre: string;
  imagen_principal_url: string | null;
  variantes: VarianteConStock[];
}

export interface RegistrarMovimientoPayload {
  producto_variante_id: number;
  tipo: TipoMovimiento;
  cantidad: number;
  motivo: string;
}

export interface ProductoResumen {
  id: number;
  nombre: string;
  imagen_principal_url: string | null;
}

export interface VarianteResumen {
  id: number;
  talla: TallaResumen;
  color: ColorResumen;
}

export interface UsuarioResumen {
  id: number;
  nombre: string;
}

export interface MovimientoOut {
  id: number;
  producto: ProductoResumen;
  variante: VarianteResumen;
  tipo: TipoMovimiento;
  cantidad: number;
  motivo: string;
  stock_anterior: number;
  stock_resultante: number;
  fecha_hora: string;
  registrado_por: UsuarioResumen;
}
