import { RolUsuario } from '../../usuarios-y-accesos/shared/models/usuario.model';

// Punto único de verdad: a qué panel pertenece cada rol reconocido.
//
// CU01 (login.ts) lo usa para decidir a dónde navegar justo después de
// iniciar sesión; NoAutorizado lo reutiliza para devolver al usuario a SU
// PROPIO panel en vez de a '/' -- ver core/pages/no-autorizado/no-autorizado.ts.
//
// Es un Record<RolUsuario, string>, no un if/else: el compilador exige que
// los 5 roles estén cubiertos. Antes, un if/else incompleto en login.ts no
// contemplaba CAJERO y caía en un `destino = '/'` por defecto -- CAJERO
// terminaba en el área pública, indistinguible de un Cliente. Con este mapa,
// agregar un rol nuevo sin registrar su ruta aquí es un error de
// compilación, no un olvido que se note recién en producción.
export const RUTA_POR_ROL: Record<RolUsuario, string> = {
  ADMINISTRADOR: '/admin',
  ENCARGADO_SUCURSAL: '/encargado',
  PROVEEDOR: '/proveedor',
  // CAJERO -- integración mínima de CU20: una pantalla puntual ("Reservas
  // pendientes de atención", ver features/cajero/reservas-pendientes), NUNCA
  // el fallback a '/' que causaba el bug original (CAJERO se veía como un
  // Cliente). Todavía no es un panel completo -- CU24 (Registrar venta) y
  // CU25 (Procesar pago) son quienes lo necesitarían, fuera de alcance.
  CAJERO: '/cajero',
  CLIENTE: '/',
};
