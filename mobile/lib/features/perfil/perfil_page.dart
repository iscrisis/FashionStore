import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../shared/widgets/async_state_message.dart';
import '../../shared/widgets/primary_button.dart';
import '../auth/auth_service.dart';
import '../auth/login_page.dart';
import '../auth/models/usuario_sesion.dart';
import '../historial_compras/mis_compras_page.dart';
import 'editar_perfil_page.dart';

/// Tab "Perfil" del bottom navigation.
///
/// Sin sesión: este widget ES directamente CU01 (Iniciar sesión) -- sin
/// ninguna pantalla intermedia de por medio. Al iniciar sesión con éxito,
/// [onSesionIniciada] actualiza el estado en AppShell y este mismo tab se
/// vuelve a construir, esta vez ya autenticado.
///
/// Con sesión de Cliente: CU04 completo -- datos reales (incluido
/// `telefono`, que CU01/CU02 no traen, por eso se consulta `GET /auth/me`
/// al entrar), "Editar perfil" y "Cerrar sesión" al final.
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

    return _PerfilAutenticado(
      usuarioInicial: usuarioActual,
      onUsuarioActualizado: onSesionIniciada,
      onCerrarSesion: onCerrarSesion,
    );
  }
}

enum _Estado { cargando, listo, error }

class _PerfilAutenticado extends StatefulWidget {
  const _PerfilAutenticado({
    required this.usuarioInicial,
    required this.onUsuarioActualizado,
    required this.onCerrarSesion,
  });

  final UsuarioSesion usuarioInicial;
  final ValueChanged<UsuarioSesion> onUsuarioActualizado;
  final VoidCallback onCerrarSesion;

  @override
  State<_PerfilAutenticado> createState() => _PerfilAutenticadoState();
}

class _PerfilAutenticadoState extends State<_PerfilAutenticado> {
  final _authService = AuthService();
  late UsuarioSesion _usuario = widget.usuarioInicial;
  _Estado _estado = _Estado.cargando;

  @override
  void initState() {
    super.initState();
    _cargarPerfil();
  }

  Future<void> _cargarPerfil() async {
    setState(() => _estado = _Estado.cargando);
    try {
      final perfil = await _authService.obtenerMiPerfil();
      if (!mounted) return;
      setState(() {
        _usuario = perfil;
        _estado = _Estado.listo;
      });
    } on SesionExpiradaError {
      // El token ya no es válido (401) o no existe -- TokenStorage ya se
      // limpió dentro de obtenerMiPerfil(). Avisamos a AppShell: al volver
      // a construir este tab, PerfilPage verá `usuario == null` y mostrará
      // Login directamente, sin romper el resto de la navegación pública.
      widget.onCerrarSesion();
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  void _abrirMisCompras() {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const MisComprasPage()));
  }

  Future<void> _abrirEdicion() async {
    final actualizado = await Navigator.of(context).push<UsuarioSesion>(
      MaterialPageRoute(builder: (_) => EditarPerfilPage(usuario: _usuario)),
    );
    if (actualizado == null) return;
    if (!mounted) return;
    setState(() => _usuario = actualizado);
    widget.onUsuarioActualizado(actualizado);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Perfil actualizado correctamente.'), backgroundColor: AppColors.burgundy),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(title: const Text('Perfil')),
      body: SafeArea(child: _buildBody()),
    );
  }

  Widget _buildBody() {
    switch (_estado) {
      case _Estado.cargando:
        return const Center(child: CircularProgressIndicator(strokeWidth: 2));
      case _Estado.error:
        return Center(
          child: AsyncStateMessage(message: 'No se pudo cargar tu perfil.', onRetry: _cargarPerfil),
        );
      case _Estado.listo:
        return ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: [
            Text('DATOS PERSONALES', style: AppTextStyles.eyebrow.copyWith(color: AppColors.burgundy)),
            const SizedBox(height: AppSpacing.sm),
            _CardDato(icon: Icons.person_outline, label: 'Nombre', valor: _usuario.nombre),
            const SizedBox(height: AppSpacing.sm),
            _CardDato(icon: Icons.mail_outline, label: 'Correo electrónico', valor: _usuario.correo),
            const SizedBox(height: AppSpacing.sm),
            _CardDato(icon: Icons.call_outlined, label: 'Teléfono', valor: _usuario.telefono ?? '—'),
            const SizedBox(height: AppSpacing.xl),
            Text('COMPRAS', style: AppTextStyles.eyebrow.copyWith(color: AppColors.burgundy)),
            const SizedBox(height: AppSpacing.sm),
            _CardAccion(
              icon: Icons.shopping_bag_outlined,
              label: 'Mis compras',
              onTap: _abrirMisCompras,
            ),
            const SizedBox(height: AppSpacing.xl),
            PrimaryButton(label: 'EDITAR PERFIL', expand: true, onPressed: _abrirEdicion),
            const SizedBox(height: AppSpacing.lg),
            OutlinedButton(
              onPressed: widget.onCerrarSesion,
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
}

/// Card navegable de una acción del perfil (ej. "Mis compras") -- mismo
/// lenguaje visual que [_CardDato] pero tappable, con chevron indicando que
/// lleva a otra pantalla.
class _CardAccion extends StatelessWidget {
  const _CardAccion({required this.icon, required this.label, required this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: AppColors.divider),
        ),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppColors.burgundy.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(AppRadius.sm),
              ),
              child: Icon(icon, size: 18, color: AppColors.burgundy),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Text(label, style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600)),
            ),
            const Icon(Icons.chevron_right, color: AppColors.textSecondary),
          ],
        ),
      ),
    );
  }
}

/// Card individual para un dato personal (Nombre / Correo / Teléfono) --
/// fondo rosado/beige suave, ícono burdeos, borde discreto. Cada dato en su
/// propia card se identifica mejor que agruparlos en un solo bloque.
class _CardDato extends StatelessWidget {
  const _CardDato({required this.icon, required this.label, required this.valor});

  final IconData icon;
  final String label;
  final String valor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.burgundy.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(AppRadius.sm),
            ),
            child: Icon(icon, size: 18, color: AppColors.burgundy),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: AppTextStyles.bodyMuted.copyWith(fontSize: 11)),
                const SizedBox(height: 2),
                Text(
                  valor,
                  style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
