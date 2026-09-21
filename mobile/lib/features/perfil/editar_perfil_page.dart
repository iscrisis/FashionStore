import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../shared/widgets/auth_header.dart';
import '../../shared/widgets/primary_button.dart';
import '../auth/auth_service.dart';
import '../auth/models/usuario_sesion.dart';

/// CU04 -- Actualizar perfil. El backend acepta nombre/correo/teléfono
/// (`ActualizarPerfilRequest`, ver backend/modules/P2_UsuariosYAccesos/
/// CU04_ActualizarPerfil/schemas.py) -- sin cambio de contraseña (eso es
/// CU03, fuera de esta fase) y sin selector de rol (el backend ni siquiera
/// lo acepta en este endpoint). En esta pantalla, a diferencia de Angular
/// (que sí deja editar el correo, ver mi-perfil.ts), el Cliente solo puede
/// editar nombre y teléfono -- el correo se muestra de solo lectura y se
/// reenvía tal cual al guardar (el backend lo exige en el body igual).
///
/// Al guardar con éxito hace `Navigator.pop(usuarioActualizado)`: Perfil
/// actualiza su vista inmediatamente con ese resultado, sin recargar ni
/// pedir cerrar/abrir sesión. "Cancelar" o la flecha de volver hacen
/// `pop()` sin argumento -- nunca se envía nada al backend si no se guardó.
class EditarPerfilPage extends StatefulWidget {
  const EditarPerfilPage({super.key, required this.usuario});

  final UsuarioSesion usuario;

  @override
  State<EditarPerfilPage> createState() => _EditarPerfilPageState();
}

class _EditarPerfilPageState extends State<EditarPerfilPage> {
  // Mismo patrón que ya exige el backend para teléfono (CU02/CU04 comparten
  // la misma regla, ver ActualizarPerfilRequest en schemas.py) -- no se
  // inventa una regla nueva para este formulario. El correo ya no se valida
  // aquí: en esta pantalla es de solo lectura (ver build()), nunca lo edita
  // el Cliente.
  static final _telefonoPattern = RegExp(r'^[0-9+\-\s()]{6,20}$');

  final _authService = AuthService();
  final _formKey = GlobalKey<FormState>();
  late final _nombreController = TextEditingController(text: widget.usuario.nombre);
  late final _telefonoController = TextEditingController(text: widget.usuario.telefono ?? '');

  bool _cargando = false;
  String? _errorMensaje;

  @override
  void dispose() {
    _nombreController.dispose();
    _telefonoController.dispose();
    super.dispose();
  }

  Future<void> _guardar() async {
    if (_cargando) return;
    final valido = _formKey.currentState?.validate() ?? false;
    if (!valido) return;

    setState(() {
      _cargando = true;
      _errorMensaje = null;
    });

    try {
      final actualizado = await _authService.actualizarMiPerfil(
        nombre: _nombreController.text.trim(),
        // El backend exige `correo` en el body (ver ActualizarPerfilRequest,
        // schemas.py) aunque esta pantalla no permita editarlo -- se
        // reenvía tal cual, nunca desde un input que el Cliente pueda tocar.
        correo: widget.usuario.correo,
        telefono: _telefonoController.text.trim(),
      );
      if (!mounted) return;
      Navigator.of(context).pop(actualizado);
    } on SesionExpiradaError {
      // La sesión ya se limpió (ver AuthService) -- se vuelve a Perfil, que
      // detectará `usuario == null` (vía AppShell) y mostrará Login.
      if (!mounted) return;
      Navigator.of(context).pop();
    } on CorreoYaRegistradoError {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _errorMensaje = 'Ya existe una cuenta registrada con este correo.';
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _errorMensaje = switch (e.statusCode) {
          422 => 'Revisa los datos ingresados e inténtalo nuevamente.',
          _ => 'No se pudo actualizar tu perfil. Inténtalo nuevamente.',
        };
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _errorMensaje = 'No se pudo conectar. Revisa tu conexión e inténtalo de nuevo.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AuthHeader(
                eyebrow: 'EDITAR PERFIL',
                mostrarVolver: true,
                onCerrar: () => Navigator.of(context).maybePop(),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(
                  AppSpacing.lg,
                  AppSpacing.xl,
                  AppSpacing.lg,
                  AppSpacing.lg,
                ),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text('Nombre', style: AppTextStyles.bodyMuted),
                      const SizedBox(height: AppSpacing.xs),
                      TextFormField(
                        controller: _nombreController,
                        textCapitalization: TextCapitalization.words,
                        textInputAction: TextInputAction.next,
                        decoration: const InputDecoration(hintText: 'Tu nombre completo'),
                        validator: (value) {
                          final texto = value?.trim() ?? '';
                          if (texto.length < 2) return 'El nombre debe tener al menos 2 caracteres.';
                          if (texto.length > 120) {
                            return 'El nombre no puede superar los 120 caracteres.';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      Text('Correo electrónico', style: AppTextStyles.bodyMuted),
                      const SizedBox(height: AppSpacing.xs),
                      _CorreoSoloLectura(correo: widget.usuario.correo),
                      const SizedBox(height: AppSpacing.lg),
                      Text('Teléfono', style: AppTextStyles.bodyMuted),
                      const SizedBox(height: AppSpacing.xs),
                      TextFormField(
                        controller: _telefonoController,
                        keyboardType: TextInputType.phone,
                        textInputAction: TextInputAction.done,
                        onFieldSubmitted: (_) => _guardar(),
                        decoration: const InputDecoration(hintText: 'Ej. 70011111'),
                        validator: (value) {
                          final texto = value?.trim() ?? '';
                          if (!_telefonoPattern.hasMatch(texto)) {
                            return 'Solo dígitos, espacios y los símbolos + - ( ).';
                          }
                          return null;
                        },
                      ),
                      if (_errorMensaje != null) ...[
                        const SizedBox(height: AppSpacing.md),
                        Container(
                          padding: const EdgeInsets.all(AppSpacing.md),
                          decoration: BoxDecoration(
                            color: AppColors.red.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(AppRadius.md),
                            border: Border.all(color: AppColors.red.withValues(alpha: 0.25)),
                          ),
                          child: Text(
                            _errorMensaje!,
                            style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy),
                          ),
                        ),
                      ],
                      const SizedBox(height: AppSpacing.xl),
                      PrimaryButton(
                        label: _cargando ? 'Guardando...' : 'GUARDAR CAMBIOS',
                        expand: true,
                        onPressed: _cargando ? null : _guardar,
                      ),
                      const SizedBox(height: AppSpacing.md),
                      Center(
                        child: TextButton(
                          onPressed: _cargando ? null : () => Navigator.of(context).maybePop(),
                          child: Text(
                            'Cancelar',
                            style: AppTextStyles.bodyMuted.copyWith(color: AppColors.textSecondary),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Correo de solo lectura -- a diferencia de Angular (que sí lo deja
/// editable, ver mi-perfil.ts), esta pantalla móvil no permite cambiarlo:
/// mismo lenguaje visual que un input (caja + radio + padding) pero con
/// fondo apagado e ícono de candado, para que se lea como deshabilitado a
/// primera vista, nunca como un campo roto o un `TextFormField` genérico.
class _CorreoSoloLectura extends StatelessWidget {
  const _CorreoSoloLectura({required this.correo});

  final String correo;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: 14),
          decoration: BoxDecoration(
            color: AppColors.divider.withValues(alpha: 0.35),
            borderRadius: BorderRadius.circular(AppRadius.md),
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  correo,
                  style: AppTextStyles.body.copyWith(color: AppColors.textSecondary),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              const Icon(Icons.lock_outline, size: 16, color: AppColors.textSecondary),
            ],
          ),
        ),
        const SizedBox(height: 4),
        Text('El correo no se puede editar desde la app.', style: AppTextStyles.bodyMuted.copyWith(fontSize: 11)),
      ],
    );
  }
}
