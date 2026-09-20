import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../auth/login_page.dart';
import '../auth/models/usuario_sesion.dart';

/// Tab "Perfil" del bottom navigation.
///
/// Sin sesión: este widget ES directamente CU01 (Iniciar sesión) -- sin
/// ninguna pantalla intermedia de por medio. Al iniciar sesión con éxito,
/// [onSesionIniciada] actualiza el estado en AppShell y este mismo tab se
/// vuelve a construir, esta vez ya autenticado -- por eso "vuelve a Perfil"
/// sin necesidad de ninguna navegación explícita.
///
/// Con sesión de Cliente: datos reales mínimos + Cerrar sesión. CU04
/// (editar perfil) queda para una fase posterior -- aquí no hay nada
/// editable ni datos inventados (avatar, dirección, puntos, etc.).
class PerfilPage extends StatelessWidget {
  const PerfilPage({
    super.key,
    required this.usuario,
    required this.onSesionIniciada,
    required this.onCerrarSesion,
  });

  final UsuarioSesion? usuario;
  final ValueChanged<UsuarioSesion> onSesionIniciada;
  final VoidCallback onCerrarSesion;

  @override
  Widget build(BuildContext context) {
    final usuarioActual = usuario;
    if (usuarioActual == null) {
      return LoginPage(onLoginExitoso: onSesionIniciada);
    }

    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(title: const Text('Perfil')),
      body: SafeArea(
        child: _ConSesion(usuario: usuarioActual, onCerrarSesion: onCerrarSesion),
      ),
    );
  }
}

class _ConSesion extends StatelessWidget {
  const _ConSesion({required this.usuario, required this.onCerrarSesion});

  final UsuarioSesion usuario;
  final VoidCallback onCerrarSesion;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      children: [
        Container(
          padding: const EdgeInsets.all(AppSpacing.lg),
          decoration: BoxDecoration(
            color: AppColors.burgundy,
            borderRadius: BorderRadius.circular(AppRadius.lg),
          ),
          child: Row(
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: AppColors.cream.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(AppRadius.md),
                ),
                child: const Icon(Icons.person_outline, color: AppColors.cream, size: 26),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      usuario.nombre,
                      style: AppTextStyles.body.copyWith(
                        color: AppColors.cream,
                        fontWeight: FontWeight.w700,
                        fontSize: 16,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      usuario.correo,
                      style: AppTextStyles.bodyMuted.copyWith(color: AppColors.cream.withValues(alpha: 0.8)),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.xl),
        OutlinedButton(
          onPressed: onCerrarSesion,
          style: OutlinedButton.styleFrom(
            foregroundColor: AppColors.red,
            side: const BorderSide(color: AppColors.red),
          ),
          child: const Text('Cerrar sesión'),
        ),
      ],
    );
  }
}
