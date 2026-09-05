// Modelos de consulta pública de sucursales (CU07) -- solo lectura, sin
// autenticación. Reutiliza los mismos datos administrados por CU06 (ciudades
// y sucursales); no los duplica. Sin "departamento": el flujo público es
// únicamente Ciudad -> Sucursal.

export interface CiudadPublica {
  id: number;
  nombre: string;
}

export interface SucursalPublica {
  id: number;
  nombre: string;
  direccion: string;
  telefono: string;
  ciudad: CiudadPublica;
}
