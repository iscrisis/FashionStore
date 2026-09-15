// Modelos exclusivos del Panel del Encargado. El backend siempre resuelve
// "mi sucursal" desde el usuario autenticado -- estos modelos nunca incluyen
// un sucursal_id que el cliente pudiera manipular.

export interface CiudadResumen {
  id: number;
  nombre: string;
}

export interface SucursalDelEncargado {
  id: number;
  nombre: string;
  ciudad: CiudadResumen;
}

export interface TallaResumen {
  id: number;
  nombre: string;
}

export interface ColorResumen {
  id: number;
  nombre: string;
}

export interface VarianteStock {
  id: number;
  talla: TallaResumen;
  color: ColorResumen;
  cantidad: number;
}

export interface TemporadaResumen {
  id: number;
  nombre: string;
}

export interface CategoriaResumen {
  id: number;
  nombre: string;
}

export interface ColeccionConTemporadaResumen {
  id: number;
  nombre: string;
  temporada: TemporadaResumen;
}

export interface ProductoInventario {
  id: number;
  nombre: string;
  // categoria/coleccion son opcionales aquí solo como tolerancia del
  // frontend: CU08 exige ambos al crear un producto (NOT NULL en la base),
  // pero un backend desactualizado podría no incluirlos todavía en la
  // respuesta -- el componente los trata como ausentes en vez de asumir
  // que siempre existen (ver inventario.ts).
  imagen_principal_url?: string | null;
  categoria?: CategoriaResumen;
  coleccion?: ColeccionConTemporadaResumen;
  variantes: VarianteStock[];
}
