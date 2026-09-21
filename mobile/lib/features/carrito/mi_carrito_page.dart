import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/storage/token_storage.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/media_url.dart';
import '../../shared/widgets/async_state_message.dart';
import '../auth/auth_service.dart';
import '../auth/login_page.dart';
import '../auth/models/usuario_sesion.dart';
import '../compra_digital/finalizar_compra_page.dart';
import 'carrito_service.dart';
import 'models/carrito.dart';

enum _Estado { verificandoSesion, sinSesion, cargando, listo, vacio, error }

/// CU21 -- Usar carrito de compras (Cliente). Tab "Carrito" del bottom nav.
///
/// Mismo patrón que CU18 (ver reservas/mis_reservas_page.dart): sin sesión
/// ES directamente CU01 (Iniciar sesión), sin pantalla intermedia; con
/// sesión, consulta SIEMPRE el backend real (`GET /carrito`) -- nunca hay un
/// carrito "de mentira" guardado localmente, FastAPI es la única fuente de
/// verdad. AppShell le asigna una `key` que cambia cada vez que el Cliente
/// vuelve a tocar este tab, para revalidar sesión y recargar en cada visita
/// (ver app_shell.dart).
///
/// El carrito NO tiene `cantidad` por item -- cada [CarritoItemOut] es una
/// unidad concreta de una variante (ver models/carrito.dart); por eso esta
/// pantalla no muestra ningún selector +/- (el backend no lo soporta, y
/// tampoco existe en Angular, ver mi-carrito.html): solo una selección
/// (checkbox) por unidad y una acción para eliminarla, igual que CU21 real.
class MiCarritoPage extends StatefulWidget {
  const MiCarritoPage({super.key, this.onExplorar});

  /// Lleva al tab "Explorar" del bottom nav -- usado por el estado vacío
  /// ("Explorar productos"). Si es null (pantalla usada fuera del shell),
  /// simplemente no se muestra esa acción.
  final VoidCallback? onExplorar;

  @override
  State<MiCarritoPage> createState() => _MiCarritoPageState();
}

class _MiCarritoPageState extends State<MiCarritoPage> {
  final _authService = AuthService();
  final _service = CarritoService();

  _Estado _estado = _Estado.verificandoSesion;
  CarritoOut? _carrito;
  int? _procesandoItemId;

  bool get _haySeleccionados => (_carrito?.items ?? const []).any((item) => item.seleccionado);

  @override
  void initState() {
    super.initState();
    _verificarSesion();
  }

  Future<void> _verificarSesion() async {
    final usuario = await _authService.sesionGuardada();
    if (!mounted) return;
    if (usuario == null) {
      setState(() => _estado = _Estado.sinSesion);
      return;
    }
    _cargarCarrito();
  }

  Future<void> _cargarCarrito() async {
    setState(() => _estado = _Estado.cargando);
    final token = await TokenStorage.getToken();
    if (token == null) {
      if (!mounted) return;
      setState(() => _estado = _Estado.sinSesion);
      return;
    }
    try {
      final carrito = await _service.consultar(token: token);
      if (!mounted) return;
      setState(() {
        _carrito = carrito;
        _estado = carrito.items.isEmpty ? _Estado.vacio : _Estado.listo;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.statusCode == 401) {
        await TokenStorage.clearSession();
        setState(() => _estado = _Estado.sinSesion);
        return;
      }
      setState(() => _estado = _Estado.error);
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  void _onLoginExitoso(UsuarioSesion usuario) {
    _cargarCarrito();
  }

  Future<void> _toggleSeleccion(CarritoItemOut item) async {
    if (_procesandoItemId != null) return;
    final token = await TokenStorage.getToken();
    if (token == null) {
      setState(() => _estado = _Estado.sinSesion);
      return;
    }
    setState(() => _procesandoItemId = item.itemId);
    try {
      final carrito = await _service.actualizarSeleccion(
        itemId: item.itemId,
        seleccionado: !item.seleccionado,
        token: token,
      );
      if (!mounted) return;
      setState(() {
        _carrito = carrito;
        _procesandoItemId = null;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _procesandoItemId = null);
      _mostrarError('No se pudo actualizar la selección. Inténtalo nuevamente.');
    }
  }

  Future<void> _eliminar(CarritoItemOut item) async {
    if (_procesandoItemId != null) return;
    final token = await TokenStorage.getToken();
    if (token == null) {
      setState(() => _estado = _Estado.sinSesion);
      return;
    }
    setState(() => _procesandoItemId = item.itemId);
    try {
      final carrito = await _service.eliminarItem(itemId: item.itemId, token: token);
      if (!mounted) return;
      setState(() {
        _carrito = carrito;
        _procesandoItemId = null;
        _estado = carrito.items.isEmpty ? _Estado.vacio : _Estado.listo;
      });
      _mostrarMensaje('Producto eliminado del carrito.');
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _procesandoItemId = null);
      _mostrarError(e.message);
    } catch (_) {
      if (!mounted) return;
      setState(() => _procesandoItemId = null);
      _mostrarError('No se pudo eliminar el producto. Inténtalo nuevamente.');
    }
  }

  void _mostrarMensaje(String texto) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(texto), backgroundColor: AppColors.burgundy),
    );
  }

  void _mostrarError(String texto) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(texto), backgroundColor: AppColors.red),
    );
  }

  // CU22 -- Realizar compra digital. "CONTINUAR COMPRA" solo navega: toda
  // la lógica de ubicación/disponibilidad/confirmación vive en
  // FinalizarCompraPage, nunca aquí (mismo criterio que ya separa CU17 de
  // CU21). Al volver, se refresca el carrito -- los items comprados siguen
  // intactos (CU22 nunca los retira, ver Models/venta.py), pero es la misma
  // recarga defensiva que ya se hace tras cualquier otra navegación.
  Future<void> _continuarCompra() async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const FinalizarCompraPage()),
    );
    if (!mounted) return;
    _cargarCarrito();
  }

  @override
  Widget build(BuildContext context) {
    if (_estado == _Estado.sinSesion) {
      return LoginPage(onLoginExitoso: _onLoginExitoso);
    }

    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(title: const Text('Carrito')),
      body: SafeArea(child: _buildBody()),
    );
  }

  Widget _buildBody() {
    switch (_estado) {
      case _Estado.sinSesion:
        return const SizedBox.shrink();
      case _Estado.verificandoSesion:
      case _Estado.cargando:
        return const Center(child: CircularProgressIndicator(strokeWidth: 2));
      case _Estado.error:
        return Center(
          child: AsyncStateMessage(
            message: 'No se pudo cargar tu carrito.',
            icon: Icons.error_outline,
            onRetry: _cargarCarrito,
          ),
        );
      case _Estado.vacio:
        return _EstadoVacio(onRefrescar: _cargarCarrito, onExplorar: widget.onExplorar);
      case _Estado.listo:
        final carrito = _carrito!;
        return Column(
          children: [
            Expanded(
              child: RefreshIndicator(
                color: AppColors.red,
                onRefresh: _cargarCarrito,
                child: ListView.separated(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  itemCount: carrito.items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.md),
                  itemBuilder: (context, index) {
                    final item = carrito.items[index];
                    return _CarritoItemCard(
                      item: item,
                      procesando: _procesandoItemId == item.itemId,
                      onToggleSeleccion: () => _toggleSeleccion(item),
                      onEliminar: () => _eliminar(item),
                    );
                  },
                ),
              ),
            ),
            _ResumenCompra(
              haySeleccionados: _haySeleccionados,
              subtotal: carrito.subtotalSeleccionado,
              onContinuar: _continuarCompra,
            ),
          ],
        );
    }
  }
}

/// "Carrito vacío" -- mismo lenguaje visual del resto de estados vacíos de
/// la app (ícono en círculo + título + mensaje), con una acción hacia el
/// catálogo -- sin inventar ningún dato ni contador.
class _EstadoVacio extends StatelessWidget {
  const _EstadoVacio({required this.onRefrescar, required this.onExplorar});

  final Future<void> Function() onRefrescar;
  final VoidCallback? onExplorar;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      color: AppColors.red,
      onRefresh: onRefrescar,
      child: LayoutBuilder(
        builder: (context, constraints) {
          return SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: ConstrainedBox(
              constraints: BoxConstraints(minHeight: constraints.maxHeight),
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 72,
                        height: 72,
                        decoration: const BoxDecoration(color: AppColors.surface, shape: BoxShape.circle),
                        child: const Icon(Icons.shopping_bag_outlined, size: 30, color: AppColors.burgundy),
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      Text('Tu carrito está vacío', style: AppTextStyles.sectionTitle, textAlign: TextAlign.center),
                      const SizedBox(height: AppSpacing.sm),
                      Text(
                        'Las prendas que agregues desde su ficha aparecerán aquí.',
                        style: AppTextStyles.bodyMuted,
                        textAlign: TextAlign.center,
                      ),
                      if (onExplorar != null) ...[
                        const SizedBox(height: AppSpacing.xl),
                        ElevatedButton(onPressed: onExplorar, child: const Text('EXPLORAR PRODUCTOS')),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

/// Tarjeta de una unidad del carrito -- selección (checkbox visual),
/// imagen, nombre, color/talla y precio (con precio anterior tachado +
/// porcentaje si está en promoción, mismo cálculo que ya trae el backend,
/// CU32). "Eliminar" es una acción secundaria discreta (texto, no un botón
/// destructivo grande) -- solo existe porque el backend realmente la
/// soporta (`DELETE /carrito/items/{id}`).
class _CarritoItemCard extends StatelessWidget {
  const _CarritoItemCard({
    required this.item,
    required this.procesando,
    required this.onToggleSeleccion,
    required this.onEliminar,
  });

  final CarritoItemOut item;
  final bool procesando;
  final VoidCallback onToggleSeleccion;
  final VoidCallback onEliminar;

  @override
  Widget build(BuildContext context) {
    final imagenUrl = MediaUrl.resolve(item.producto.imagenPrincipalUrl);
    final seleccionado = item.seleccionado;

    return Opacity(
      opacity: procesando ? 0.6 : 1,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(color: seleccionado ? AppColors.red.withValues(alpha: 0.5) : AppColors.divider),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            GestureDetector(
              onTap: procesando ? null : onToggleSeleccion,
              behavior: HitTestBehavior.opaque,
              child: Padding(
                padding: const EdgeInsets.only(top: 2, right: AppSpacing.sm),
                child: Icon(
                  seleccionado ? Icons.check_circle : Icons.circle_outlined,
                  size: 22,
                  color: seleccionado ? AppColors.red : AppColors.textSecondary,
                ),
              ),
            ),
            ClipRRect(
              borderRadius: BorderRadius.circular(AppRadius.sm),
              child: Container(
                width: 64,
                height: 64,
                color: AppColors.cream,
                child: imagenUrl != null
                    ? Image.network(
                        imagenUrl,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => const _ImagenPlaceholder(),
                      )
                    : const _ImagenPlaceholder(),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.producto.nombre,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${item.variante.color.nombre} · Talla ${item.variante.talla.nombre}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTextStyles.bodyMuted,
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Wrap(
                    crossAxisAlignment: WrapCrossAlignment.center,
                    spacing: AppSpacing.xs,
                    children: [
                      Text(
                        'Bs ${item.precioUnitario.toStringAsFixed(2)}',
                        style: (item.enPromocion ? AppTextStyles.priceDiscount : AppTextStyles.price)
                            .copyWith(fontSize: 14),
                      ),
                      if (item.enPromocion) ...[
                        Text('Bs ${item.precioBase.toStringAsFixed(2)}', style: AppTextStyles.priceStrike),
                        if (item.porcentajeDescuento != null)
                          Text(
                            '-${item.porcentajeDescuento!.toStringAsFixed(0)}%',
                            style: AppTextStyles.bodyMuted.copyWith(color: AppColors.red, fontWeight: FontWeight.w600),
                          ),
                      ],
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  GestureDetector(
                    onTap: procesando ? null : onEliminar,
                    child: Text(
                      'Eliminar',
                      style: AppTextStyles.bodyMuted.copyWith(
                        color: AppColors.textSecondary,
                        decoration: TextDecoration.underline,
                        decorationColor: AppColors.textSecondary,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ImagenPlaceholder extends StatelessWidget {
  const _ImagenPlaceholder();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Icon(Icons.checkroom_outlined, size: 22, color: AppColors.textSecondary),
    );
  }
}

/// Barra inferior fija -- subtotal de lo SELECCIONADO (nunca calculado en
/// Flutter, siempre el valor que ya devuelve el backend) + "CONTINUAR
/// COMPRA". Sin nada seleccionado, el botón se reemplaza por un mensaje --
/// nunca queda un CTA activo sin ningún producto detrás. CU22 (compra
/// digital) todavía no se implementa: el botón queda preparado, pero solo
/// avisa que la compra estará disponible pronto.
class _ResumenCompra extends StatelessWidget {
  const _ResumenCompra({required this.haySeleccionados, required this.subtotal, required this.onContinuar});

  final bool haySeleccionados;
  final double subtotal;
  final VoidCallback onContinuar;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(
        AppSpacing.lg,
        AppSpacing.md,
        AppSpacing.lg,
        AppSpacing.md + MediaQuery.of(context).padding.bottom,
      ),
      decoration: BoxDecoration(
        color: AppColors.cream,
        border: const Border(top: BorderSide(color: AppColors.divider)),
      ),
      child: haySeleccionados
          ? Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Subtotal seleccionado', style: AppTextStyles.bodyMuted),
                    Text(
                      'Bs ${subtotal.toStringAsFixed(2)}',
                      style: AppTextStyles.price.copyWith(fontSize: 18),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.sm),
                ElevatedButton(onPressed: onContinuar, child: const Text('CONTINUAR COMPRA')),
              ],
            )
          : Center(
              child: Text('Selecciona una prenda para continuar.', style: AppTextStyles.bodyMuted),
            ),
    );
  }
}
