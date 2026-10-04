import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/storage/token_storage.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_radius.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/utils/media_url.dart';
import '../../catalogo/catalogo_service.dart';
import '../../catalogo/producto_detalle_page.dart';
import '../asistente_ia_service.dart';
import '../models/mensaje_asistente.dart';

const _saludoInicial = '¡Hola! Soy el asistente de FashionStore. ¿Qué estás buscando?';
const _mensajeErrorRed =
    'El asistente no está disponible en este momento. Puedes seguir explorando nuestro catálogo.';
// Mismo tope que el backend (ver schemas.MensajeAsistenteRequest.historial,
// y asistente-ia.ts en Angular) -- se recorta también acá para no mandar un
// payload más grande del que el backend igualmente va a recortar.
const _maxTurnosHistorial = 6;

/// CU29 -- Obtener recomendaciones mediante IA (Cliente/Invitado), versión
/// móvil. Botón flotante + panel de chat superpuestos sobre el shell de
/// navegación (ver features/shell/app_shell.dart) -- igual que en Angular
/// (montado fuera del `<router-outlet>`, en public-layout), este widget
/// vive por encima del `IndexedStack` de tabs, así que la conversación
/// sobrevive mientras el Cliente cambia entre Inicio/Explorar/Reservas/
/// Carrito/Perfil.
///
/// Flutter NUNCA llama a Gemini -- solo a POST /asistente-ia/mensaje (ver
/// AsistenteIaService). El historial de esta sesión vive SOLO en este
/// State, nunca en una tabla propia -- si se cierra la app, se pierde y
/// vuelve a empezar con el saludo inicial (mismo criterio que Angular).
///
/// Los productos que trae cada respuesta son SIEMPRE los que ya validó
/// FastAPI contra PostgreSQL -- "VER" navega al detalle REAL del producto
/// (mismo `ProductoDetallePage` que usa el catálogo), nunca agrega al
/// carrito ni implementa otro detalle desde acá.
class AsistenteIaOverlay extends StatefulWidget {
  const AsistenteIaOverlay({super.key});

  @override
  State<AsistenteIaOverlay> createState() => _AsistenteIaOverlayState();
}

class _AsistenteIaOverlayState extends State<AsistenteIaOverlay> {
  final _service = AsistenteIaService();
  final _catalogoService = CatalogoService();
  final _controller = TextEditingController();
  final _scrollController = ScrollController();

  bool _abierto = false;
  bool _enviando = false;
  bool _cargandoProducto = false;
  final List<MensajeChat> _mensajes = [
    const MensajeChat(rol: RolMensajeChat.asistente, texto: _saludoInicial),
  ];

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _alternar() => setState(() => _abierto = !_abierto);

  void _cerrar() {
    if (_abierto) setState(() => _abierto = false);
  }

  void _scrollAlFinal() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _enviar() async {
    final texto = _controller.text.trim();
    if (texto.isEmpty || _enviando) return;

    // Historial ANTES de agregar este mensaje -- son los turnos previos que
    // le dan contexto a Gemini, el mensaje actual va aparte (ver
    // MensajeAsistenteRequest en el backend).
    final desde = _mensajes.length > _maxTurnosHistorial ? _mensajes.length - _maxTurnosHistorial : 0;
    final historial = _mensajes.skip(desde).map((m) => TurnoChat(rol: m.rol, texto: m.texto)).toList();

    setState(() {
      _mensajes.add(MensajeChat(rol: RolMensajeChat.usuario, texto: texto));
      _controller.clear();
      _enviando = true;
    });
    _scrollAlFinal();

    try {
      final token = await TokenStorage.getToken();
      final respuesta = await _service.enviarMensaje(mensaje: texto, historial: historial, token: token);
      if (!mounted) return;
      setState(() {
        _mensajes.add(MensajeChat(
          rol: RolMensajeChat.asistente,
          texto: respuesta.respuesta,
          productos: respuesta.productos,
        ));
        _enviando = false;
      });
    } on ApiException {
      if (!mounted) return;
      setState(() {
        _mensajes.add(const MensajeChat(rol: RolMensajeChat.asistente, texto: _mensajeErrorRed));
        _enviando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _mensajes.add(const MensajeChat(rol: RolMensajeChat.asistente, texto: _mensajeErrorRed));
        _enviando = false;
      });
    } finally {
      _scrollAlFinal();
    }
  }

  Future<void> _verProducto(ProductoRecomendado producto) async {
    if (_cargandoProducto) return;
    setState(() => _cargandoProducto = true);
    try {
      final completo = await _catalogoService.obtenerProducto(producto.id);
      if (!mounted) return;
      _cerrar();
      await Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => ProductoDetallePage(producto: completo)),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No se pudo abrir el producto: ${e.message}')),
      );
    } finally {
      if (mounted) setState(() => _cargandoProducto = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    return Stack(
      children: [
        if (_abierto)
          Positioned(
            left: AppSpacing.md,
            right: AppSpacing.md,
            bottom: 96,
            top: mediaQuery.padding.top + AppSpacing.xxl,
            child: _ChatPanel(
              mensajes: _mensajes,
              enviando: _enviando,
              controller: _controller,
              scrollController: _scrollController,
              onEnviar: _enviar,
              onCerrar: _cerrar,
              onVerProducto: _verProducto,
            ),
          ),
        Positioned(
          right: AppSpacing.md,
          bottom: AppSpacing.md,
          child: _BotonFlotante(abierto: _abierto, onPressed: _alternar),
        ),
      ],
    );
  }
}

class _BotonFlotante extends StatelessWidget {
  const _BotonFlotante({required this.abierto, required this.onPressed});

  final bool abierto;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return FloatingActionButton(
      heroTag: 'asistente-ia-boton',
      backgroundColor: AppColors.burgundy,
      foregroundColor: AppColors.cream,
      tooltip: abierto ? 'Cerrar asistente de FashionStore' : 'Abrir asistente de FashionStore',
      onPressed: onPressed,
      child: Icon(abierto ? Icons.close : Icons.auto_awesome),
    );
  }
}

class _ChatPanel extends StatelessWidget {
  const _ChatPanel({
    required this.mensajes,
    required this.enviando,
    required this.controller,
    required this.scrollController,
    required this.onEnviar,
    required this.onCerrar,
    required this.onVerProducto,
  });

  final List<MensajeChat> mensajes;
  final bool enviando;
  final TextEditingController controller;
  final ScrollController scrollController;
  final VoidCallback onEnviar;
  final VoidCallback onCerrar;
  final ValueChanged<ProductoRecomendado> onVerProducto;

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 8,
      borderRadius: BorderRadius.circular(AppRadius.lg),
      color: AppColors.cream,
      child: Column(
        children: [
          _Header(onCerrar: onCerrar),
          const Divider(height: 1),
          Expanded(
            child: ListView.builder(
              controller: scrollController,
              padding: const EdgeInsets.all(AppSpacing.md),
              itemCount: mensajes.length + (enviando ? 1 : 0),
              itemBuilder: (context, index) {
                if (index >= mensajes.length) {
                  return const _BurbujaEscribiendo();
                }
                final mensaje = mensajes[index];
                return _Burbuja(mensaje: mensaje, onVerProducto: onVerProducto);
              },
            ),
          ),
          const Divider(height: 1),
          _InputRow(controller: controller, enviando: enviando, onEnviar: onEnviar),
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.onCerrar});

  final VoidCallback onCerrar;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(AppSpacing.md, AppSpacing.sm, AppSpacing.xs, AppSpacing.sm),
      child: Row(
        children: [
          const Icon(Icons.auto_awesome, size: 18, color: AppColors.burgundy),
          const SizedBox(width: AppSpacing.sm),
          const Expanded(child: Text('Asistente FashionStore', style: AppTextStyles.sectionTitle)),
          IconButton(
            onPressed: onCerrar,
            icon: const Icon(Icons.close),
            tooltip: 'Cerrar asistente',
          ),
        ],
      ),
    );
  }
}

class _BurbujaEscribiendo extends StatelessWidget {
  const _BurbujaEscribiendo();

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: AppSpacing.sm),
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              width: 12,
              height: 12,
              child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.textSecondary),
            ),
            SizedBox(width: AppSpacing.sm),
            Text('Escribiendo…', style: AppTextStyles.bodyMuted),
          ],
        ),
      ),
    );
  }
}

class _Burbuja extends StatelessWidget {
  const _Burbuja({required this.mensaje, required this.onVerProducto});

  final MensajeChat mensaje;
  final ValueChanged<ProductoRecomendado> onVerProducto;

  @override
  Widget build(BuildContext context) {
    final esUsuario = mensaje.rol == RolMensajeChat.usuario;
    return Align(
      alignment: esUsuario ? Alignment.centerRight : Alignment.centerLeft,
      child: Column(
        crossAxisAlignment: esUsuario ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Container(
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.72),
            margin: const EdgeInsets.only(bottom: AppSpacing.sm),
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm),
            decoration: BoxDecoration(
              color: esUsuario ? AppColors.burgundy : AppColors.surface,
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: Text(
              mensaje.texto,
              style: AppTextStyles.body.copyWith(color: esUsuario ? AppColors.cream : AppColors.charcoal),
            ),
          ),
          if (mensaje.productos != null && mensaje.productos!.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: Column(
                children: mensaje.productos!
                    .map((producto) => _ProductoChatCard(producto: producto, onVer: () => onVerProducto(producto)))
                    .toList(),
              ),
            ),
        ],
      ),
    );
  }
}

class _ProductoChatCard extends StatelessWidget {
  const _ProductoChatCard({required this.producto, required this.onVer});

  final ProductoRecomendado producto;
  final VoidCallback onVer;

  @override
  Widget build(BuildContext context) {
    final imagenUrl = MediaUrl.resolve(producto.imagenPrincipalUrl);
    return Container(
      width: MediaQuery.of(context).size.width * 0.72,
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: AppColors.cream,
        border: Border.all(color: AppColors.divider),
        borderRadius: BorderRadius.circular(AppRadius.sm),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(AppRadius.sm),
            child: SizedBox(
              width: 48,
              height: 48,
              child: imagenUrl != null
                  ? Image.network(imagenUrl, fit: BoxFit.cover)
                  : const ColoredBox(
                      color: AppColors.surface,
                      child: Icon(Icons.checkroom, size: 18, color: AppColors.textSecondary),
                    ),
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(producto.nombre, style: AppTextStyles.body, maxLines: 1, overflow: TextOverflow.ellipsis),
                if (producto.color != null || producto.talla != null)
                  Text(
                    [
                      if (producto.color != null) producto.color!,
                      if (producto.talla != null) 'Talla ${producto.talla}',
                    ].join(' · '),
                    style: AppTextStyles.bodyMuted,
                  ),
                Row(
                  children: [
                    if (producto.enPromocion)
                      Padding(
                        padding: const EdgeInsets.only(right: AppSpacing.xs),
                        child: Text('Bs ${producto.precioBase.toStringAsFixed(2)}', style: AppTextStyles.priceStrike),
                      ),
                    Text(
                      'Bs ${producto.precioFinal.toStringAsFixed(2)}',
                      style: producto.enPromocion ? AppTextStyles.priceDiscount : AppTextStyles.price,
                    ),
                  ],
                ),
                if (producto.disponibilidadResumen != null)
                  Text(producto.disponibilidadResumen!, style: AppTextStyles.bodyMuted, maxLines: 1, overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
          TextButton(onPressed: onVer, child: const Text('VER')),
        ],
      ),
    );
  }
}

class _InputRow extends StatelessWidget {
  const _InputRow({required this.controller, required this.enviando, required this.onEnviar});

  final TextEditingController controller;
  final bool enviando;
  final VoidCallback onEnviar;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.sm),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              enabled: !enviando,
              maxLength: 500,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => onEnviar(),
              decoration: const InputDecoration(
                hintText: 'Escribe tu mensaje...',
                counterText: '',
                isDense: true,
              ),
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          IconButton.filled(
            onPressed: enviando ? null : onEnviar,
            icon: const Icon(Icons.arrow_upward),
            style: IconButton.styleFrom(backgroundColor: AppColors.red, foregroundColor: AppColors.cream),
          ),
        ],
      ),
    );
  }
}
