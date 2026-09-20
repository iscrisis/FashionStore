import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../shared/widgets/auth_header.dart';
import '../../shared/widgets/primary_button.dart';
import 'auth_service.dart';
import 'models/usuario_sesion.dart';
import 'registro_page.dart';

/// CU01 -- Iniciar sesión. Nunca es la pantalla inicial de la app -- Home
/// pública sigue siendo el punto de entrada.
///
/// Dos formas de usarse, ambas válidas:
/// - Empotrada (sin `Navigator.push`): así la usa hoy el tab Perfil cuando
///   no hay sesión -- Perfil literalmente ES este widget, sin pantalla
///   intermedia. En ese caso se pasa [onLoginExitoso] y no hay nada que
///   "volver" (no se muestra flecha de retroceso).
/// - Empujada con `Navigator.push` (futuro: Reservar/Carrito/Comprar
///   pidiendo sesión): sin [onLoginExitoso], hace `Navigator.pop(usuario)`
///   al iniciar sesión con éxito, y sí muestra flecha de retroceso porque
///   hay una pantalla anterior a la que volver.
class LoginPage extends StatefulWidget {
  const LoginPage({super.key, this.onLoginExitoso});

  final ValueChanged<UsuarioSesion>? onLoginExitoso;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _authService = AuthService();
  final _formKey = GlobalKey<FormState>();
  final _correoController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _cargando = false;
  bool _passwordVisible = false;
  String? _errorMensaje;

  @override
  void dispose() {
    _correoController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _iniciarSesion() async {
    if (_cargando) return;
    final formValido = _formKey.currentState?.validate() ?? false;
    if (!formValido) return;

    setState(() {
      _cargando = true;
      _errorMensaje = null;
    });

    try {
      final usuario = await _authService.iniciarSesion(
        correo: _correoController.text.trim(),
        password: _passwordController.text,
      );
      if (!mounted) return;
      final onLoginExitoso = widget.onLoginExitoso;
      if (onLoginExitoso != null) {
        onLoginExitoso(usuario);
      } else {
        Navigator.of(context).pop(usuario);
      }
    } on RolNoPermitidoError {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _errorMensaje = 'Esta aplicación móvil está disponible para clientes. '
            'Utiliza la plataforma web para acceder a tu cuenta.';
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _cargando = false;
        _errorMensaje = switch (e.statusCode) {
          401 => 'Correo o contraseña incorrectos.',
          403 => 'Tu cuenta está inhabilitada. Contacta al administrador.',
          _ => 'No se pudo iniciar sesión. Inténtalo nuevamente.',
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
                eyebrow: 'INICIAR SESIÓN',
                mostrarVolver: Navigator.canPop(context),
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
                      Text('Correo electrónico', style: AppTextStyles.bodyMuted),
                      const SizedBox(height: AppSpacing.xs),
                      // Ambos campos DEBEN vivir dentro de un mismo
                      // AutofillGroup: sin él, el autocompletado de
                      // Android puede rellenar visualmente el campo sin
                      // que el TextEditingController reciba ese mismo
                      // valor -- el campo se ve lleno, pero lo que
                      // realmente se envía a FastAPI puede ser otra cosa
                      // (o quedar vacío/obsoleto). Este es exactamente el
                      // tipo de bug que hace fallar credenciales reales
                      // solo en Flutter, nunca en la web.
                      AutofillGroup(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            TextFormField(
                              controller: _correoController,
                              keyboardType: TextInputType.emailAddress,
                              textInputAction: TextInputAction.next,
                              autocorrect: false,
                              autofillHints: const [AutofillHints.email],
                              decoration: const InputDecoration(hintText: 'tucorreo@ejemplo.com'),
                              validator: (value) {
                                final texto = value?.trim() ?? '';
                                if (texto.isEmpty) return 'Ingresa tu correo.';
                                if (!texto.contains('@') || !texto.contains('.')) {
                                  return 'Ingresa un correo válido.';
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
                              textInputAction: TextInputAction.done,
                              autocorrect: false,
                              enableSuggestions: false,
                              autofillHints: const [AutofillHints.password],
                              onFieldSubmitted: (_) => _iniciarSesion(),
                              decoration: InputDecoration(
                                hintText: 'Tu contraseña',
                                suffixIcon: IconButton(
                                  onPressed: () => setState(() => _passwordVisible = !_passwordVisible),
                                  icon: Icon(
                                    _passwordVisible
                                        ? Icons.visibility_off_outlined
                                        : Icons.visibility_outlined,
                                    color: AppColors.textSecondary,
                                  ),
                                ),
                              ),
                              validator: (value) {
                                if (value == null || value.isEmpty) return 'Ingresa tu contraseña.';
                                return null;
                              },
                            ),
                          ],
                        ),
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
                        label: _cargando ? 'Ingresando...' : 'Iniciar sesión',
                        expand: true,
                        onPressed: _cargando ? null : _iniciarSesion,
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      Center(
                        child: TextButton(
                          onPressed: _cargando
                              ? null
                              : () => Navigator.of(context).push(
                                    MaterialPageRoute(builder: (_) => const RegistroPage()),
                                  ),
                          child: Text.rich(
                            TextSpan(
                              text: '¿No tienes una cuenta? ',
                              style: AppTextStyles.bodyMuted,
                              children: [
                                TextSpan(
                                  text: 'Crear cuenta',
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
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
