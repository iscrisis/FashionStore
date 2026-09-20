/// Refleja `UsuarioPublico` (CU01 -- backend/modules/P2_UsuariosYAccesos/
/// CU01_IniciarSesion/schemas.py): nunca incluye password ni password_hash.
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
  });

  final int id;
  final String nombre;
  final String correo;
  final String rol;

  bool get esCliente => rol == 'CLIENTE';

  factory UsuarioSesion.fromJson(Map<String, dynamic> json) {
    return UsuarioSesion(
      id: json['id'] as int,
      nombre: json['nombre'] as String,
      correo: json['correo'] as String,
      rol: json['rol'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'nombre': nombre,
        'correo': correo,
        'rol': rol,
      };
}
