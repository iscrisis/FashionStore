import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/storage/token_storage.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/media_url.dart';
import '../auth/auth_service.dart';
import '../auth/login_page.dart';
import '../auth/models/usuario_sesion.dart';
import '../carrito/carrito_service.dart';
import '../disponibilidad/disponibilidad_service.dart';
import '../disponibilidad/models/disponibilidad_sucursal.dart';
import '../reservas/models/reserva.dart';
import '../reservas/widgets/crear_reserva_sheet.dart';
import '../reservas/widgets/reserva_confirmacion_dialog.dart';
import '../sucursales/models/ciudad.dart';
import '../sucursales/sucursales_service.dart';
import '../vestidor_virtual/models/prenda_virtual.dart';
import '../vestidor_virtual/vestidor_virtual_page.dart';
import 'models/producto.dart';

/// Detalle de un producto ya cargado por el catálogo (CU11) -- reutiliza el
/// objeto [Producto] que ya trae la lista, sin golpear un endpoint nuevo
/// para lo básico. Integra además CU07 (ciudades), CU12 (disponibilidad por
/// sucursal), CU17 (crear reserva) y CU21 (carrito), siguiendo el MISMO
/// flujo que ya usa la web: seleccionar color + talla -> Agregar al carrito
/// y/o elegir sucursal con disponibilidad -> Reservar.
class ProductoDetallePage extends StatefulWidget {
  const ProductoDetallePage({super.key, required this.producto});

  final Producto producto;

  @override
  State<ProductoDetallePage> createState() => _ProductoDetallePageState();
}

class _ProductoDetallePageState extends State<ProductoDetallePage> {
  final _sucursalesService = SucursalesService();
  final _disponibilidadService = DisponibilidadService();

  late final List<String> _galeria = _construirGaleria(widget.producto);
  int _indiceActual = 0;

  // Talla/color SIEMPRE tienen una selección (por defecto, la primera del
  // producto) -- a diferencia de una simple etiqueta informativa, aquí
  // determinan la variante real que se consulta en disponibilidad, igual
  // que en producto-detalle.ts de Angular (tallaSeleccionadaId/
  // colorSeleccionadoId nunca quedan sin valor si el producto tiene tallas
  // o colores).
  late int? _tallaSeleccionadaId =
      widget.producto.tallas.isNotEmpty ? widget.producto.tallas.first.id : null;
  late int? _colorSeleccionadoId =
      widget.producto.colores.isNotEmpty ? widget.producto.colores.first.id : null;

  // La ciudad, en cambio, nace en null a propósito (igual que en Angular):
  // nunca se autoselecciona la primera de la lista sin que el Cliente la
  // elija -- mostrar disponibilidad de una ciudad no elegida sería confuso.
  List<Ciudad> _ciudades = [];
  bool _cargandoCiudades = true;
  int? _ciudadSeleccionadaId;

  List<DisponibilidadSucursal> _disponibilidad = [];
  bool _cargandoDisponibilidad = false;
  bool _errorDisponibilidad = false;

  // Variantes del producto (talla+color -> producto_variante_id), SIN
  // filtrar por ciudad -- CU12 acepta `ciudad_id` opcional (ver
  // DisponibilidadService.consultar) y, sin él, igual devuelve todas las
  // sucursales activas con el `producto_variante_id` de cada variante (el
  // id es el mismo en cualquier sucursal, solo cambia `cantidad`). Se carga
  // UNA vez al abrir la ficha, en paralelo con las ciudades, para que
  // "Agregar al carrito" (CU21) no dependa de que el Cliente haya elegido
  // ciudad/sucursal -- esa selección es SOLO del flujo de Reservar (CU17).
  List<DisponibilidadSucursal> _disponibilidadGlobal = [];

  // CU17 (crear reserva): sucursal que el propio Cliente eligió tocando una
  // tarjeta de "Disponibilidad por sucursal" -- a diferencia de talla/color
  // (atributos del producto), la sucursal no tiene un valor por defecto:
  // nace en null y solo el Cliente la fija. Se reinicia cuando cambia
  // talla, color o ciudad porque la disponibilidad ya no es la misma.
  int? _sucursalSeleccionadaId;
  bool _reservando = false;

  // CU21 (agregar al carrito): no depende de sucursal/fecha/hora, solo de
  // la variante (color+talla) ya elegida arriba -- por eso vive con su
  // propio flag de carga, independiente de `_reservando`.
  bool _agregandoAlCarrito = false;

  @override
  void initState() {
    super.initState();
    _cargarCiudades();
    _cargarVariantesProducto();
  }

  /// Resuelve `producto_variante_id` para CADA combinación talla+color del
  /// producto, sin depender de que el Cliente elija ciudad -- ver
  /// `_disponibilidadGlobal`. Un fallo aquí simplemente deja "Agregar al
  /// carrito" deshabilitado (mismo criterio silencioso que `_cargarCiudades`
  /// ya usa): no hay nada que reintentar manualmente, se resuelve solo si
  /// el Cliente reabre la ficha.
  Future<void> _cargarVariantesProducto() async {
    try {
      final resultado = await _disponibilidadService.consultar(productoId: widget.producto.id);
      if (!mounted) return;
      setState(() => _disponibilidadGlobal = resultado.disponibilidad);
    } catch (_) {
      // Silencioso a propósito -- ver docstring del método.
    }
  }

  List<String> _construirGaleria(Producto producto) {
    final urls = <String>[];
    final principal = producto.imagenPrincipalUrl;
    if (principal != null && principal.isNotEmpty) {
      urls.add(principal);
    }
    final adicionales = [...producto.imagenes]..sort((a, b) => a.orden.compareTo(b.orden));
    for (final imagen in adicionales) {
      if (!urls.contains(imagen.url)) {
        urls.add(imagen.url);
      }
    }
    return urls;
  }

  Future<void> _cargarCiudades() async {
    try {
      final ciudades = await _sucursalesService.listarCiudades();
      if (!mounted) return;
      setState(() {
        _ciudades = ciudades;
        _cargandoCiudades = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _cargandoCiudades = false);
    }
  }

  void _seleccionarTalla(int id) {
    if (_tallaSeleccionadaId == id) return;
    // No hace falta volver a consultar CU12: la respuesta ya cargada trae
    // TODAS las variantes del producto por sucursal -- cambiar de talla solo
    // cambia qué variante se lee de esa misma lista (ver
    // DisponibilidadSucursal.varianteDe), no qué se pide al backend.
    setState(() {
      _tallaSeleccionadaId = id;
      _sucursalSeleccionadaId = null;
    });
  }

  void _seleccionarColor(int id) {
    if (_colorSeleccionadoId == id) return;
    setState(() {
      _colorSeleccionadoId = id;
      _sucursalSeleccionadaId = null;
    });
  }

  void _seleccionarCiudad(int? ciudadId) {
    setState(() {
      _ciudadSeleccionadaId = ciudadId;
      _disponibilidad = [];
      _errorDisponibilidad = false;
      _sucursalSeleccionadaId = null;
    });
    if (ciudadId != null) {
      _cargarDisponibilidad();
    }
  }

  Future<void> _cargarDisponibilidad() async {
    final tallaId = _tallaSeleccionadaId;
    final colorId = _colorSeleccionadoId;
    final ciudadId = _ciudadSeleccionadaId;
    if (ciudadId == null) return;

    setState(() {
      _cargandoDisponibilidad = true;
      _errorDisponibilidad = false;
    });
    try {
      final resultado = await _disponibilidadService.consultar(
        productoId: widget.producto.id,
        tallaId: tallaId,
        colorId: colorId,
        ciudadId: ciudadId,
      );
      if (!mounted) return;
      setState(() {
        _disponibilidad = resultado.disponibilidad;
        _cargandoDisponibilidad = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cargandoDisponibilidad = false;
        _errorDisponibilidad = true;
      });
    }
  }

  // Variante real (id) que corresponde a la talla+color elegidos arriba --
  // se resuelve desde `_disponibilidadGlobal` (SIN filtrar por ciudad,
  // ProductoVariante es global: el id es el mismo en cualquier sucursal,
  // solo cambia `cantidad`) a propósito, para que esta variante quede
  // disponible ANTES de elegir ciudad/sucursal -- "Agregar al carrito"
  // (CU21) la usa así; "Reservar" (CU17) además exige `_sucursalSeleccionadaId`
  // por separado, así que igual espera a que el Cliente elija sucursal real
  // con stock (ver `_buildDisponibilidad`, que sí lee `_disponibilidad`
  // ciudad-scoped para el estado Disponible/Agotado de cada tarjeta). null
  // si CU12 todavía no respondió o esa combinación no existe.
  int? get _varianteSeleccionadaId {
    final tallaId = _tallaSeleccionadaId;
    final colorId = _colorSeleccionadoId;
    if (tallaId == null || colorId == null) return null;
    for (final item in _disponibilidadGlobal) {
      final variante = item.varianteDe(tallaId: tallaId, colorId: colorId);
      if (variante != null) return variante.productoVarianteId;
    }
    return null;
  }

  String? get _sucursalSeleccionadaNombre {
    final id = _sucursalSeleccionadaId;
    if (id == null) return null;
    for (final item in _disponibilidad) {
      if (item.sucursalId == id) return item.sucursal;
    }
    return null;
  }

  String? get _tallaSeleccionadaNombre {
    final id = _tallaSeleccionadaId;
    if (id == null) return null;
    for (final talla in widget.producto.tallas) {
      if (talla.id == id) return talla.nombre;
    }
    return null;
  }

  String? get _colorSeleccionadoNombre {
    final id = _colorSeleccionadoId;
    if (id == null) return null;
    for (final color in widget.producto.colores) {
      if (color.id == id) return color.nombre;
    }
    return null;
  }

  void _seleccionarSucursal(int sucursalId, bool disponible) {
    if (!disponible) return;
    setState(() => _sucursalSeleccionadaId = sucursalId);
  }

  // CU17 -- Crear reserva de prendas. El botón "Reservar" solo se habilita
  // con producto+variante+sucursal ya elegidos (ver _buildDisponibilidad).
  // La navegación sigue siendo pública hasta este punto: recién aquí, al
  // presionar "Reservar", se verifica sesión -- sin sesión se empuja Login
  // (CU01) y, si el Cliente inicia sesión con éxito, el flujo CONTINÚA
  // directo hacia el modal de fecha/hora en vez de volver a Home.
  Future<void> _reservar() async {
    final varianteId = _varianteSeleccionadaId;
    final sucursalId = _sucursalSeleccionadaId;
    final sucursalNombre = _sucursalSeleccionadaNombre;
    if (varianteId == null || sucursalId == null || sucursalNombre == null || _reservando) {
      return;
    }

    setState(() => _reservando = true);
    try {
      final token = await _obtenerTokenOPedirLogin();
      if (token == null || !mounted) return;

      final reserva = await showModalBottomSheet<ReservaOut>(
        context: context,
        isScrollControlled: true,
        backgroundColor: AppColors.cream,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(AppRadius.lg)),
        ),
        builder: (_) => CrearReservaSheet(
          productoVarianteId: varianteId,
          productoNombre: widget.producto.nombre,
          productoImagenUrl: MediaUrl.resolve(widget.producto.imagenPrincipalUrl),
          tallaNombre: _tallaSeleccionadaNombre ?? '',
          colorNombre: _colorSeleccionadoNombre ?? '',
          sucursalId: sucursalId,
          sucursalNombre: sucursalNombre,
          token: token,
        ),
      );
      if (reserva == null || !mounted) return;

      await showDialog<void>(
        context: context,
        builder: (_) => ReservaConfirmacionDialog(reserva: reserva),
      );
      if (!mounted) return;

      // La reserva acaba de comprometer stock (stock_reservado, ver
      // backend) -- se refresca la disponibilidad para que las tarjetas de
      // sucursal dejen de mostrar como "Disponible" una unidad que este
      // mismo Cliente ya reservó. La sucursal elegida se limpia: el botón
      // "Reservar" vuelve a su estado inicial, listo para una reserva
      // nueva, sin ocultarse nunca.
      setState(() => _sucursalSeleccionadaId = null);
      _cargarDisponibilidad();
    } finally {
      if (mounted) setState(() => _reservando = false);
    }
  }

  /// Sesión ya guardada (ver TokenStorage) o, si no hay ninguna, empuja
  /// LoginPage (CU01) y espera su resultado. `null` significa "el Cliente
  /// canceló el login" -- en ese caso `_reservar` no continúa a ningún
  /// lado, ni siquiera a Home: simplemente se queda en el detalle del
  /// producto, exactamente donde estaba.
  Future<String?> _obtenerTokenOPedirLogin() async {
    final sesion = await AuthService().sesionGuardada();
    if (sesion != null) return TokenStorage.getToken();

    if (!mounted) return null;
    final usuario = await Navigator.of(context).push<UsuarioSesion>(
      MaterialPageRoute(builder: (_) => const LoginPage()),
    );
    if (usuario == null) return null;
    return TokenStorage.getToken();
  }

  // CU21 -- Agregar al carrito. Convive con "Reservar" (CU17) sin tocar su
  // lógica: solo necesita la variante (color+talla) ya elegida arriba,
  // nunca ciudad/sucursal/fecha/hora. Mismo patrón de sesión que _reservar:
  // sin sesión pide Login y, tras iniciar sesión con éxito, agrega
  // directamente -- nunca navega a Home ni pierde la selección.
  Future<void> _agregarAlCarrito() async {
    final varianteId = _varianteSeleccionadaId;
    if (varianteId == null || _agregandoAlCarrito) return;

    setState(() => _agregandoAlCarrito = true);
    try {
      final token = await _obtenerTokenOPedirLogin();
      if (token == null || !mounted) return;

      await CarritoService().agregarItem(productoVarianteId: varianteId, token: token);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Producto agregado al carrito.'), backgroundColor: AppColors.burgundy),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_esDisponibilidadLimitada(e) ? 'Disponibilidad limitada' : e.message),
          backgroundColor: AppColors.red,
        ),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No se pudo agregar el producto al carrito. Inténtalo nuevamente.'),
          backgroundColor: AppColors.red,
        ),
      );
    } finally {
      if (mounted) setState(() => _agregandoAlCarrito = false);
    }
  }

  /// CU21 -- el backend rechaza `POST /carrito/items` con 422 cuando ninguna
  /// sucursal activa cubre la cantidad pedida (ver
  /// CU21_UsarCarritoCompras/service.py, StockInsuficienteError); ese mensaje
  /// real ("No hay disponibilidad suficiente para esa cantidad.") es
  /// correcto pero técnico para el Cliente final -- esta función SOLO decide
  /// qué texto mostrar, nunca oculta ni reinterpreta la respuesta real: el
  /// backend sigue siendo la única fuente de verdad, Flutter solo cambia la
  /// presentación de ESTE caso puntual. Otros 422 (ej. variante inexistente)
  /// siguen mostrando el mensaje real del backend, sin tocar.
  bool _esDisponibilidadLimitada(ApiException e) {
    return e.statusCode == 422 && e.message.toLowerCase().contains('disponibilidad');
  }

  // Último caso de uso -- "Utilizar vestidor virtual mediante cámara móvil".
  // Solo necesita la talla/color YA elegidos arriba (siempre tienen un
  // valor, ver comentario de _tallaSeleccionadaId/_colorSeleccionadoId):
  // no depende de ciudad, sucursal ni de ninguna llamada a disponibilidad,
  // así que puede abrirse en cualquier momento de la ficha.
  void _probarVirtualmente() {
    final producto = widget.producto;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => VestidorVirtualPage(
          prenda: PrendaVirtual(
            productoId: producto.id,
            nombre: producto.nombre,
            categoriaNombre: producto.categoria.nombre,
            tallaNombre: _tallaSeleccionadaNombre ?? 'Talla única',
            colorNombre: _colorSeleccionadoNombre ?? 'Color único',
            imagenCatalogoUrl: MediaUrl.resolve(producto.imagenPrincipalUrl),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final producto = widget.producto;
    final imagenActual = _galeria.isEmpty ? null : MediaUrl.resolve(_galeria[_indiceActual]);

    return Scaffold(
      appBar: AppBar(title: Text(producto.nombre)),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(AppRadius.lg),
                child: AspectRatio(
                  aspectRatio: 3 / 4,
                  child: Container(
                    color: AppColors.surface,
                    child: imagenActual != null
                        ? Image.network(
                            imagenActual,
                            fit: BoxFit.cover,
                            errorBuilder: (_, _, _) => const _Placeholder(),
                          )
                        : const _Placeholder(),
                  ),
                ),
              ),
              if (_galeria.length > 1) ...[
                const SizedBox(height: AppSpacing.sm),
                SizedBox(
                  height: 64,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: _galeria.length,
                    separatorBuilder: (_, _) => const SizedBox(width: AppSpacing.sm),
                    itemBuilder: (context, index) {
                      final seleccionada = index == _indiceActual;
                      final miniatura = MediaUrl.resolve(_galeria[index]);
                      return GestureDetector(
                        onTap: () => setState(() => _indiceActual = index),
                        behavior: HitTestBehavior.opaque,
                        child: Container(
                          width: 64,
                          height: 64,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(AppRadius.sm),
                            color: AppColors.surface,
                            border: Border.all(
                              color: seleccionada ? AppColors.red : AppColors.divider,
                              width: seleccionada ? 2 : 1,
                            ),
                          ),
                          clipBehavior: Clip.antiAlias,
                          child: miniatura != null
                              ? Image.network(
                                  miniatura,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, _, _) => const _MiniPlaceholder(),
                                )
                              : const _MiniPlaceholder(),
                        ),
                      );
                    },
                  ),
                ),
              ],
              const SizedBox(height: AppSpacing.lg),
              Text(producto.categoria.nombre.toUpperCase(), style: AppTextStyles.eyebrow),
              const SizedBox(height: AppSpacing.xs),
              Text(producto.nombre, style: AppTextStyles.display.copyWith(fontSize: 22)),
              const SizedBox(height: AppSpacing.sm),
              Wrap(
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: AppSpacing.sm,
                children: [
                  Text(
                    'Bs ${producto.precioFinal.toStringAsFixed(2)}',
                    style: (producto.enPromocion ? AppTextStyles.priceDiscount : AppTextStyles.price)
                        .copyWith(fontSize: 20),
                  ),
                  if (producto.enPromocion) ...[
                    Text('Bs ${producto.precioBase.toStringAsFixed(2)}', style: AppTextStyles.priceStrike),
                    if (producto.porcentajeDescuento != null)
                      Text(
                        '-${producto.porcentajeDescuento!.toStringAsFixed(0)}%',
                        style: AppTextStyles.bodyMuted.copyWith(
                          color: AppColors.red,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                  ],
                ],
              ),
              if (producto.descripcion != null && producto.descripcion!.trim().isNotEmpty) ...[
                const SizedBox(height: AppSpacing.lg),
                Text(producto.descripcion!, style: AppTextStyles.body),
              ],
              if (producto.colores.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.lg),
                Text('Color', style: AppTextStyles.sectionTitle.copyWith(fontSize: 15)),
                const SizedBox(height: AppSpacing.sm),
                Wrap(
                  spacing: AppSpacing.sm,
                  runSpacing: AppSpacing.sm,
                  children: producto.colores.map((color) {
                    final seleccionado = _colorSeleccionadoId == color.id;
                    return _VarianteChip(
                      label: color.nombre,
                      selected: seleccionado,
                      onTap: () => _seleccionarColor(color.id),
                    );
                  }).toList(),
                ),
              ],
              if (producto.tallas.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.lg),
                Text('Talla', style: AppTextStyles.sectionTitle.copyWith(fontSize: 15)),
                const SizedBox(height: AppSpacing.sm),
                Wrap(
                  spacing: AppSpacing.sm,
                  runSpacing: AppSpacing.sm,
                  children: producto.tallas.map((talla) {
                    final seleccionada = _tallaSeleccionadaId == talla.id;
                    return _VarianteChip(
                      label: talla.nombre,
                      selected: seleccionada,
                      onTap: () => _seleccionarTalla(talla.id),
                    );
                  }).toList(),
                ),
              ],

              // Último caso de uso -- "Probar virtualmente" abre el vestidor
              // virtual (cámara + overlay) con la talla/color ya elegidos
              // arriba. Vive antes de "Agregar al carrito" porque en el
              // flujo el Cliente prueba la prenda ANTES de decidir
              // comprarla o reservarla.
              const SizedBox(height: AppSpacing.lg),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _probarVirtualmente,
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.burgundy,
                    side: const BorderSide(color: AppColors.burgundy),
                  ),
                  icon: const Icon(Icons.camera_alt_outlined, size: 18),
                  label: const Text('PROBAR VIRTUALMENTE'),
                ),
              ),

              // CU21 -- Agregar al carrito. Vive junto a "Reservar" (CU17),
              // sin tocar su lógica -- secundario (contorno rojo, no
              // relleno) para no competir con el CTA principal de reserva
              // que aparece más abajo. Solo requiere la variante elegida
              // arriba; no depende de ciudad/sucursal.
              if (producto.tallas.isNotEmpty || producto.colores.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.lg),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: (_varianteSeleccionadaId != null && !_agregandoAlCarrito)
                        ? _agregarAlCarrito
                        : null,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.red,
                      side: const BorderSide(color: AppColors.red),
                    ),
                    icon: const Icon(Icons.shopping_bag_outlined, size: 18),
                    label: Text(_agregandoAlCarrito ? 'Agregando...' : 'AGREGAR AL CARRITO'),
                  ),
                ),
              ],

              // CU12 -- Consultar disponibilidad por sucursal. Solo tiene
              // sentido si el producto tiene variantes reales que consultar.
              if (producto.tallas.isNotEmpty && producto.colores.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.xl),
                Text(
                  'Disponibilidad por sucursal',
                  style: AppTextStyles.sectionTitle.copyWith(fontSize: 15),
                ),
                const SizedBox(height: AppSpacing.sm),
                _SelectorCiudad(
                  ciudades: _ciudades,
                  ciudadSeleccionadaId: _ciudadSeleccionadaId,
                  cargando: _cargandoCiudades,
                  onChanged: _seleccionarCiudad,
                ),
                const SizedBox(height: AppSpacing.md),
                _buildDisponibilidad(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDisponibilidad() {
    if (_ciudadSeleccionadaId == null) {
      return Text(
        'Selecciona una ciudad para ver la disponibilidad.',
        style: AppTextStyles.bodyMuted,
      );
    }
    if (_cargandoDisponibilidad) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: AppSpacing.lg),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      );
    }
    if (_errorDisponibilidad) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('No se pudo consultar la disponibilidad.', style: AppTextStyles.bodyMuted),
          TextButton(onPressed: _cargarDisponibilidad, child: const Text('Reintentar')),
        ],
      );
    }
    if (_disponibilidad.isEmpty) {
      return Text('Sin sucursales en esta ciudad.', style: AppTextStyles.bodyMuted);
    }

    final tallaId = _tallaSeleccionadaId;
    final colorId = _colorSeleccionadoId;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ..._disponibilidad.map((item) {
          final variante = (tallaId != null && colorId != null)
              ? item.varianteDe(tallaId: tallaId, colorId: colorId)
              : null;
          final disponible = (variante?.cantidad ?? 0) > 0;
          return Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.sm),
            child: _SucursalDisponibilidadCard(
              sucursal: item.sucursal,
              disponible: disponible,
              seleccionada: item.sucursalId == _sucursalSeleccionadaId,
              onTap: () => _seleccionarSucursal(item.sucursalId, disponible),
            ),
          );
        }),
        // CU17 -- Reservar. Solo aparece cuando ya hay variante+sucursal
        // elegidas (el mismo "Selecciona una sucursal disponible" que ya
        // usa Angular como título del botón deshabilitado, ver
        // crear-reserva.html). Un único botón principal -- nunca varios
        // iguales.
        const SizedBox(height: AppSpacing.sm),
        ElevatedButton.icon(
          onPressed: (_sucursalSeleccionadaId != null && !_reservando) ? _reservar : null,
          icon: const Icon(Icons.event_available_outlined, size: 18),
          label: Text(_reservando ? 'Un momento...' : 'Reservar'),
        ),
      ],
    );
  }
}

/// Chip de selección única (talla/color) -- siempre hay exactamente una
/// seleccionada, no es un toggle libre: determina la variante real que se
/// consulta en disponibilidad.
class _VarianteChip extends StatelessWidget {
  const _VarianteChip({required this.label, required this.selected, required this.onTap});

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
        decoration: BoxDecoration(
          color: selected ? AppColors.red : AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.pill),
          border: Border.all(color: selected ? AppColors.red : AppColors.divider),
        ),
        child: Text(
          label,
          style: AppTextStyles.bodyMuted.copyWith(
            color: selected ? AppColors.cream : AppColors.charcoal,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }
}

/// Selector de ciudad (CU07 -- reutiliza `SucursalesService.listarCiudades`,
/// la misma fuente real que ya usa Angular). Crema con borde burdeos, sin
/// autoseleccionar ninguna ciudad.
class _SelectorCiudad extends StatelessWidget {
  const _SelectorCiudad({
    required this.ciudades,
    required this.ciudadSeleccionadaId,
    required this.cargando,
    required this.onChanged,
  });

  final List<Ciudad> ciudades;
  final int? ciudadSeleccionadaId;
  final bool cargando;
  final ValueChanged<int?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.burgundy, width: 1.2),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<int>(
          value: ciudadSeleccionadaId,
          isExpanded: true,
          hint: Text(
            cargando ? 'Cargando ciudades...' : 'Selecciona una ciudad',
            style: AppTextStyles.body.copyWith(color: AppColors.textSecondary),
          ),
          icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.burgundy),
          dropdownColor: AppColors.cream,
          items: ciudades
              .map(
                (ciudad) => DropdownMenuItem<int>(
                  value: ciudad.id,
                  child: Text(ciudad.nombre, style: AppTextStyles.body),
                ),
              )
              .toList(),
          onChanged: (cargando || ciudades.isEmpty) ? null : onChanged,
        ),
      ),
    );
  }
}

/// Card compacta de sucursal dentro de disponibilidad: solo nombre + estado
/// (Disponible/Agotado) -- no dirección ni teléfono, no aportan en este
/// contexto ("¿dónde está disponible esta prenda?"). Burdeos para
/// "Disponible" (identidad FashionStore, sin usar verde).
///
/// CU17 (crear reserva): además de mostrar disponibilidad, esta MISMA
/// tarjeta es la forma de elegir la sucursal donde reservar -- no existe
/// ninguna pantalla aparte de sucursales para esto (ver
/// producto_detalle_page.dart, `_seleccionarSucursal`). Solo es tocable si
/// `disponible`; el relleno rojo indica la sucursal ya elegida.
class _SucursalDisponibilidadCard extends StatelessWidget {
  const _SucursalDisponibilidadCard({
    required this.sucursal,
    required this.disponible,
    required this.seleccionada,
    required this.onTap,
  });

  final String sucursal;
  final bool disponible;
  final bool seleccionada;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: disponible ? onTap : null,
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm + 2),
        decoration: BoxDecoration(
          color: seleccionada ? AppColors.red.withValues(alpha: 0.08) : AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(
            color: seleccionada
                ? AppColors.red
                : (disponible ? AppColors.burgundy.withValues(alpha: 0.35) : AppColors.divider),
            width: seleccionada ? 1.4 : 1,
          ),
        ),
        child: Row(
          children: [
            Icon(
              seleccionada ? Icons.check_circle : Icons.storefront_outlined,
              size: 16,
              color: seleccionada ? AppColors.red : AppColors.burgundy,
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Text(
                sucursal,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w500),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: disponible ? AppColors.burgundy : AppColors.divider,
                borderRadius: BorderRadius.circular(AppRadius.pill),
              ),
              child: Text(
                disponible ? 'Disponible' : 'Agotado',
                style: AppTextStyles.bodyMuted.copyWith(
                  color: disponible ? AppColors.cream : AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                  fontSize: 11,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Placeholder extends StatelessWidget {
  const _Placeholder();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Icon(Icons.checkroom_outlined, size: 48, color: AppColors.textSecondary),
    );
  }
}

class _MiniPlaceholder extends StatelessWidget {
  const _MiniPlaceholder();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Icon(Icons.checkroom_outlined, size: 20, color: AppColors.textSecondary),
    );
  }
}
