/// Refleja `UsuarioPublico` (CU01) y, cuando viene de CU04 (`GET`/`PUT
/// /auth/me`), también `telefono` (`MiPerfilResponse` = `UsuarioPublico` +
/// `telefono`, ver backend/modules/P2_UsuariosYAccesos/
/// CU04_ActualizarPerfil/schemas.py). Nunca incluye password ni
/// password_hash.
///
/// `telefono` es `null` cuando este objeto viene del login/registro (CU01/
/// CU02 no lo devuelven) -- Perfil lo completa consultando `/auth/me`.
///
/// `rol` usa exactamente los valores reales de `RolUsuario`
/// (backend/modules/P2_UsuariosYAccesos/Models/rol.py): ADMINISTRADOR,
/// ENCARGADO_SUCURSAL, CAJERO, CLIENTE, PROVEEDOR.
class UsuarioSesion {
  const UsuarioSesion({
    required this.id,
    required this.nombre,
    required this.correo,
    required this.rol,
    this.telefono,
  });

  final int id;
  final String nombre;
  final String correo;
  final String rol;
  final String? telefono;

  bool get esCliente => rol == 'CLIENTE';

  factory UsuarioSesion.fromJson(Map<String, dynamic> json) {
    return UsuarioSesion(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      correo: json['correo'] as String,
      rol: json['rol'] as String,
      telefono: json['telefono'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'nombre': nombre,
        'correo': correo,
        'rol': rol,
        if (telefono != null) 'telefono': telefono,
      };
}
