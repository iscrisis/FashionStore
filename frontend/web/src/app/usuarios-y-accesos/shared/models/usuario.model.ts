// Entidad Usuario, compartida por todo el paquete "usuarios-y-accesos".
// CU01 (iniciar sesión) es el primer consumidor. CU02, CU03, CU04 y CU05
// reutilizarán este mismo modelo — no debe duplicarse por caso de uso.

export type RolUsuario = 'ADMINISTRADOR' | 'ENCARGADO_SUCURSAL' | 'CAJERO' | 'PROVEEDOR' | 'CLIENTE';

export interface Usuario {
  id: number;
  nombre: string;
  correo: string;
  rol: RolUsuario;
}

export interface LoginRequest {
  correo: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  usuario: Usuario;
}

// CU03 -- Recuperar contraseña.
export interface ForgotPasswordRequest {
  correo: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
  confirmar_password: string;
}

export interface MensajeGenericoResponse {
  message: string;
}
