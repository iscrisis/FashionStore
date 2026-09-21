import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../shared/widgets/auth_header.dart';
import '../../shared/widgets/primary_button.dart';
import 'auth_service.dart';

/// CU03 -- Recuperar contraseña. Se abre únicamente desde CU01 (Login ->
/// "¿Olvidaste tu contraseña?").
///
/// El flujo real del backend es por ENLACE de un solo paso dentro de la
/// app: el Cliente pide el enlace aquí (`POST /auth/forgot-password`);
/// FastAPI le envía un correo cuyo enlace abre
/// `{FRONTEND_URL}/restablecer-contrasena?token=...` -- una página de
/// Angular, no una pantalla de Flutter (ver PasswordResetService.solicitar,
/// backend/modules/P2_UsuariosYAccesos/CU03_RecuperarContrasena/
/// service.py). Por eso esta pantalla NO pide token ni nueva contraseña:
/// completar el restablecimiento ocurre en el navegador. Implementar esa
/// segunda pantalla aquí simularía un flujo que el backend no tiene.
class RecuperarPasswordPage extends StatefulWidget {
  const RecuperarPasswordPage({super.key});

  @override
  State<RecuperarPasswordPage> createState() => _RecuperarPasswordPageState();
}

class _RecuperarPasswordPageState extends State<RecuperarPasswordPage> {
  static final _correoPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

  final _authService = AuthService();
  final _formKey = GlobalKey<FormState>();
  final _correoController = TextEditingController();

  bool _cargando = false;
  bool _enviado = false;
  String _mensaje = '';
  String? _errorMensaje;

  @override
  void dispose() {
    _correoController.dispose();
    super.dispose();
  }

  Future<void> _enviar() async {
    if (_cargando) return;
    final valido = _formKey.currentState?.validate() ?? false;
    if (!valido) return;

    setState(() {
      _cargando = true;
      _errorMensaje = null;
    });

    try {
      // El backend responde 200 exista o no la cuenta -- nunca se revela
      // "correo no encontrado" (ver AuthService.solicitarRecuperacion).
      final mensaje = await _authService.solicitarRecuperacion(
        correo: _correoController.text.trim(),
      );
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _enviado = true;
        _mensaje = mensaje;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _errorMensaje = switch (e.statusCode) {
          422 => 'Ingresa un correo válido.',
          _ => 'No se pudo procesar tu solicitud. Inténtalo nuevamente.',
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
                eyebrow: 'RECUPERAR CONTRASEÑA',
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
                child: _enviado ? _buildExito() : _buildFormulario(),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildExito() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(AppSpacing.lg),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(AppRadius.lg),
            border: Border.all(color: AppColors.burgundy.withValues(alpha: 0.2)),
          ),
          child: Column(
            children: [
              Container(
                width: 56,
                height: 56,
                decoration: const BoxDecoration(color: AppColors.burgundy, shape: BoxShape.circle),
                child: const Icon(Icons.mark_email_read_outlined, color: AppColors.cream, size: 26),
              ),
              const SizedBox(height: AppSpacing.md),
              Text('Revisa tu correo', style: AppTextStyles.sectionTitle, textAlign: TextAlign.center),
              const SizedBox(height: AppSpacing.sm),
              Text(_mensaje, style: AppTextStyles.bodyMuted, textAlign: TextAlign.center),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.xl),
        PrimaryButton(
          label: 'Volver a iniciar sesión',
          expand: true,
          onPressed: () => Navigator.of(context).pop(),
        ),
      ],
    );
  }

  Widget _buildFormulario() {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Ingresa tu correo y te enviaremos instrucciones para restablecer '
            'tu contraseña.',
            style: AppTextStyles.body,
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Correo electrónico', style: AppTextStyles.bodyMuted),
          const SizedBox(height: AppSpacing.xs),
          TextFormField(
            controller: _correoController,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.done,
            autocorrect: false,
            onFieldSubmitted: (_) => _enviar(),
            decoration: const InputDecoration(hintText: 'tucorreo@ejemplo.com'),
            validator: (value) {
              final texto = value?.trim() ?? '';
              if (texto.isEmpty || !_correoPattern.hasMatch(texto)) {
                return 'Ingresa un correo válido.';
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
              child: Text(_errorMensaje!, style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy)),
            ),
          ],
          const SizedBox(height: AppSpacing.xl),
          PrimaryButton(
            label: _cargando ? 'Enviando...' : 'ENVIAR',
            expand: true,
            onPressed: _cargando ? null : _enviar,
          ),
        ],
      ),
    );
  }
}
