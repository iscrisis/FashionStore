import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../shared/widgets/auth_header.dart';
import '../../shared/widgets/primary_button.dart';
import 'auth_service.dart';

/// CU02 -- Registrar cliente. Siempre se abre empujada desde CU01 (Login ->
/// "Crear cuenta"): al terminar, vuelve a ese mismo Login (`Navigator.pop`)
/// para que el Cliente recién creado inicie sesión por separado -- el
/// backend no emite JWT en /auth/register a propósito (ver
/// CU02_RegistrarCliente/router.py), así que aquí NUNCA se guarda una
/// sesión.
///
/// Reglas de validación replicadas EXACTAMENTE de
/// RegistroClienteRequest (backend/modules/P2_UsuariosYAccesos/
/// CU02_RegistrarCliente/schemas.py) para que el Cliente vea el error antes
/// de golpear la red, no porque Flutter decida su propia regla.
class RegistroPage extends StatefulWidget {
  const RegistroPage({super.key});

  @override
  State<RegistroPage> createState() => _RegistroPageState();
}

class _RegistroPageState extends State<RegistroPage> {
  static final _correoPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
  static final _telefonoPattern = RegExp(r'^[0-9+\-\s()]{6,20}$');

  final _authService = AuthService();
  final _formKey = GlobalKey<FormState>();
  final _nombreController = TextEditingController();
  final _correoController = TextEditingController();
  final _telefonoController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmarController = TextEditingController();

  bool _cargando = false;
  bool _passwordVisible = false;
  bool _confirmarVisible = false;
  bool _registroExitoso = false;
  String? _errorMensaje;

  @override
  void dispose() {
    _nombreController.dispose();
    _correoController.dispose();
    _telefonoController.dispose();
    _passwordController.dispose();
    _confirmarController.dispose();
    super.dispose();
  }

  Future<void> _registrar() async {
    if (_cargando) return;
    final valido = _formKey.currentState?.validate() ?? false;
    if (!valido) return;

    setState(() {
      _cargando = true;
      _errorMensaje = null;
    });

    try {
      await _authService.registrarCliente(
        nombre: _nombreController.text.trim(),
        correo: _correoController.text.trim(),
        telefono: _telefonoController.text.trim(),
        password: _passwordController.text,
        confirmarPassword: _confirmarController.text,
      );
      if (!mounted) return;
      // Nunca conservar la contraseña en memoria más de lo necesario.
      _passwordController.clear();
      _confirmarController.clear();
      setState(() {
        _cargando = false;
        _registroExitoso = true;
      });
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
        // 422: la validación real del backend rechazó algo que la
        // validación local (idéntica a la suya) no debería dejar pasar --
        // FastAPI devuelve una lista de errores técnica, no un mensaje
        // apto para mostrar tal cual (ver ApiClient, no se modifica).
        _errorMensaje = switch (e.statusCode) {
          422 => 'Revisa los datos ingresados e inténtalo nuevamente.',
          _ => 'No se pudo crear la cuenta. Inténtalo nuevamente.',
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
                eyebrow: 'CREAR CUENTA',
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
                child: _registroExitoso ? _buildExito() : _buildFormulario(),
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
                child: const Icon(Icons.check, color: AppColors.cream, size: 28),
              ),
              const SizedBox(height: AppSpacing.md),
              Text('Cuenta creada', style: AppTextStyles.sectionTitle, textAlign: TextAlign.center),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'Tu cuenta se creó correctamente. Ahora puedes iniciar sesión.',
                style: AppTextStyles.bodyMuted,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.xl),
        PrimaryButton(
          label: 'Iniciar sesión',
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
          Text('Nombre', style: AppTextStyles.bodyMuted),
          const SizedBox(height: AppSpacing.xs),
          TextFormField(
            controller: _nombreController,
            textInputAction: TextInputAction.next,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(hintText: 'Tu nombre completo'),
            validator: (value) {
              final texto = value?.trim() ?? '';
              if (texto.length < 2) return 'El nombre debe tener al menos 2 caracteres.';
              if (texto.length > 120) return 'El nombre no puede superar los 120 caracteres.';
              return null;
            },
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Correo electrónico', style: AppTextStyles.bodyMuted),
          const SizedBox(height: AppSpacing.xs),
          TextFormField(
            controller: _correoController,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            autocorrect: false,
            decoration: const InputDecoration(hintText: 'tucorreo@ejemplo.com'),
            validator: (value) {
              final texto = value?.trim() ?? '';
              if (texto.isEmpty || !_correoPattern.hasMatch(texto)) {
                return 'Ingresa un correo válido.';
              }
              return null;
            },
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Teléfono', style: AppTextStyles.bodyMuted),
          const SizedBox(height: AppSpacing.xs),
          TextFormField(
            controller: _telefonoController,
            keyboardType: TextInputType.phone,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(hintText: 'Ej. 70011111'),
            validator: (value) {
              final texto = value?.trim() ?? '';
              if (!_telefonoPattern.hasMatch(texto)) {
                return 'Solo dígitos, espacios y los símbolos + - ( ).';
              }
              return null;
            },
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Contraseña', style: AppTextStyles.bodyMuted),
          const SizedBox(height: AppSpacing.xs),
          TextFormField(
            controller: _passwordController,
            obscureText: !_passwordVisible,
            textInputAction: TextInputAction.next,
            autocorrect: false,
            enableSuggestions: false,
            decoration: InputDecoration(
              hintText: 'Mínimo 8 caracteres',
              suffixIcon: IconButton(
                onPressed: () => setState(() => _passwordVisible = !_passwordVisible),
                icon: Icon(
                  _passwordVisible ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                  color: AppColors.textSecondary,
                ),
              ),
            ),
            validator: (value) {
              if (value == null || value.length < 8) {
                return 'La contraseña debe tener al menos 8 caracteres.';
              }
              return null;
            },
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Confirmar contraseña', style: AppTextStyles.bodyMuted),
          const SizedBox(height: AppSpacing.xs),
          TextFormField(
            controller: _confirmarController,
            obscureText: !_confirmarVisible,
            textInputAction: TextInputAction.done,
            autocorrect: false,
            enableSuggestions: false,
            onFieldSubmitted: (_) => _registrar(),
            decoration: InputDecoration(
              hintText: 'Repite tu contraseña',
              suffixIcon: IconButton(
                onPressed: () => setState(() => _confirmarVisible = !_confirmarVisible),
                icon: Icon(
                  _confirmarVisible ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                  color: AppColors.textSecondary,
                ),
              ),
            ),
            validator: (value) {
              if (value != _passwordController.text) return 'Las contraseñas no coinciden.';
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
            label: _cargando ? 'Creando cuenta...' : 'CREAR CUENTA',
            expand: true,
            onPressed: _cargando ? null : _registrar,
          ),
          const SizedBox(height: AppSpacing.lg),
          Center(
            child: TextButton(
              onPressed: _cargando ? null : () => Navigator.of(context).maybePop(),
              child: Text.rich(
                TextSpan(
                  text: '¿Ya tienes una cuenta? ',
                  style: AppTextStyles.bodyMuted,
                  children: [
                    TextSpan(
                      text: 'Iniciar sesión',
                      style: AppTextStyles.bodyMuted.copyWith(
                        color: AppColors.red,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
