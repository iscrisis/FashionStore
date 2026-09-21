import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../shared/widgets/async_state_message.dart';
import '../../shared/widgets/primary_button.dart';
import '../../shared/widgets/product_card.dart';
import 'catalogo_service.dart';
import 'models/coleccion.dart';
import 'models/color_opcion.dart';
import 'models/producto.dart';
import 'models/talla.dart';
import 'producto_detalle_page.dart';

enum _Estado { cargando, listo, vacio, error }

/// Catálogo completo (CU11), opcionalmente filtrado por categoría o
/// colección -- reutilizado desde la Home ("Ver todos", categorías,
/// colección destacada, sección Colecciones), desde "Ver todas" de
/// colecciones y desde el tab "Explorar" de la navegación inferior.
/// Público: no requiere sesión.
///
/// Para colecciones se prefiere pasar [coleccion] (el objeto real que ya
/// trae nombre + temporada desde /catalogo/colecciones) en vez de
/// [coleccionId]+[titulo] sueltos: así esta pantalla puede mostrar también
/// la temporada real, sin volver a consultarla ni inventarla.
class CatalogoPage extends StatefulWidget {
  const CatalogoPage({
    super.key,
    this.categoriaId,
    this.coleccionId,
    this.coleccion,
    this.titulo = 'Explorar',
  });

  final int? categoriaId;
  final int? coleccionId;
  final Coleccion? coleccion;
  final String titulo;

  int? get _coleccionIdEfectivo => coleccion?.id ?? coleccionId;
  String get _tituloEfectivo => coleccion?.nombre ?? titulo;

  @override
  State<CatalogoPage> createState() => _CatalogoPageState();
}

class _CatalogoPageState extends State<CatalogoPage> {
  final _catalogoService = CatalogoService();
  final _searchController = TextEditingController();

  _Estado _estado = _Estado.cargando;
  List<Producto> _productos = [];

  // Filtros reales soportados por CU11 (GET /catalogo/productos?talla_id=
  // &color_id=), además de categoria_id/coleccion_id/search ya usados. Las
  // listas de opciones se cargan una sola vez, al abrir el panel de filtros.
  int? _tallaId;
  int? _colorId;
  List<Talla>? _tallasDisponibles;
  List<ColorOpcion>? _coloresDisponibles;

  bool get _hayFiltrosActivos => _tallaId != null || _colorId != null;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _cargar() async {
    setState(() => _estado = _Estado.cargando);
    try {
      final productos = await _catalogoService.listarProductos(
        categoriaId: widget.categoriaId,
        coleccionId: widget._coleccionIdEfectivo,
        tallaId: _tallaId,
        colorId: _colorId,
        search: _searchController.text,
      );
      if (!mounted) return;
      setState(() {
        _productos = productos;
        _estado = productos.isEmpty ? _Estado.vacio : _Estado.listo;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  Future<void> _abrirFiltros() async {
    try {
      _tallasDisponibles ??= await _catalogoService.listarTallas();
      _coloresDisponibles ??= await _catalogoService.listarColores();
    } catch (_) {
      // Si fallan las listas de opciones, simplemente no se puede filtrar
      // ahora -- el catálogo ya cargado sigue intacto, no se rompe la
      // pantalla por esto.
      return;
    }
    if (!mounted) return;

    int? tallaSeleccionada = _tallaId;
    int? colorSeleccionado = _colorId;

    await showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppColors.cream,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(AppRadius.lg)),
      ),
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (sheetContext, setSheetState) {
            return Padding(
              padding: EdgeInsets.fromLTRB(
                AppSpacing.lg,
                AppSpacing.lg,
                AppSpacing.lg,
                AppSpacing.lg + MediaQuery.of(sheetContext).viewInsets.bottom,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Filtros', style: AppTextStyles.sectionTitle),
                      TextButton(
                        onPressed: () => setSheetState(() {
                          tallaSeleccionada = null;
                          colorSeleccionado = null;
                        }),
                        child: const Text('Limpiar'),
                      ),
                    ],
                  ),
                  if (_tallasDisponibles!.isNotEmpty) ...[
                    const SizedBox(height: AppSpacing.sm),
                    Text('Talla', style: AppTextStyles.bodyMuted),
                    const SizedBox(height: AppSpacing.sm),
                    Wrap(
                      spacing: AppSpacing.sm,
                      runSpacing: AppSpacing.sm,
                      children: _tallasDisponibles!.map((talla) {
                        final seleccionado = tallaSeleccionada == talla.id;
                        return FilterChip(
                          label: Text(talla.nombre),
                          selected: seleccionado,
                          onSelected: (_) => setSheetState(() {
                            tallaSeleccionada = seleccionado ? null : talla.id;
                          }),
                          selectedColor: AppColors.red,
                          backgroundColor: AppColors.surface,
                          checkmarkColor: AppColors.cream,
                          labelStyle: AppTextStyles.bodyMuted.copyWith(
                            color: seleccionado ? AppColors.cream : AppColors.charcoal,
                            fontWeight: FontWeight.w500,
                          ),
                          side: BorderSide.none,
                        );
                      }).toList(),
                    ),
                  ],
                  if (_coloresDisponibles!.isNotEmpty) ...[
                    const SizedBox(height: AppSpacing.lg),
                    Text('Color', style: AppTextStyles.bodyMuted),
                    const SizedBox(height: AppSpacing.sm),
                    Wrap(
                      spacing: AppSpacing.sm,
                      runSpacing: AppSpacing.sm,
                      children: _coloresDisponibles!.map((color) {
                        final seleccionado = colorSeleccionado == color.id;
                        return FilterChip(
                          label: Text(color.nombre),
                          selected: seleccionado,
                          onSelected: (_) => setSheetState(() {
                            colorSeleccionado = seleccionado ? null : color.id;
                          }),
                          selectedColor: AppColors.red,
                          backgroundColor: AppColors.surface,
                          checkmarkColor: AppColors.cream,
                          labelStyle: AppTextStyles.bodyMuted.copyWith(
                            color: seleccionado ? AppColors.cream : AppColors.charcoal,
                            fontWeight: FontWeight.w500,
                          ),
                          side: BorderSide.none,
                        );
                      }).toList(),
                    ),
                  ],
                  const SizedBox(height: AppSpacing.lg),
                  PrimaryButton(
                    label: 'Aplicar filtros',
                    expand: true,
                    onPressed: () {
                      setState(() {
                        _tallaId = tallaSeleccionada;
                        _colorId = colorSeleccionado;
                      });
                      Navigator.of(sheetContext).pop();
                      _cargar();
                    },
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final coleccion = widget.coleccion;

    return Scaffold(
      appBar: AppBar(title: Text(widget._tituloEfectivo)),
      body: SafeArea(
        child: Column(
          children: [
            if (coleccion != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, 0),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Temporada: ${coleccion.temporada.nombre}',
                    style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy),
                  ),
                ),
              ),
            Padding(
              padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, AppSpacing.md),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _searchController,
                      onSubmitted: (_) => _cargar(),
                      textInputAction: TextInputAction.search,
                      decoration: const InputDecoration(
                        hintText: 'Buscar prendas...',
                        prefixIcon: Icon(Icons.search),
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Container(
                    decoration: BoxDecoration(
                      color: _hayFiltrosActivos ? AppColors.red : AppColors.surface,
                      borderRadius: BorderRadius.circular(AppRadius.md),
                    ),
                    child: IconButton(
                      onPressed: _abrirFiltros,
                      tooltip: 'Filtros',
                      icon: Icon(
                        Icons.tune,
                        color: _hayFiltrosActivos ? AppColors.cream : AppColors.charcoal,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    switch (_estado) {
      case _Estado.cargando:
        return const Center(child: CircularProgressIndicator(strokeWidth: 2));
      case _Estado.error:
        return Center(
          child: AsyncStateMessage(message: 'No se pudo cargar el catálogo.', onRetry: _cargar),
        );
      case _Estado.vacio:
        return const Center(
          child: AsyncStateMessage(
            message: 'No se encontraron prendas con estos criterios.',
            icon: Icons.checkroom_outlined,
          ),
        );
      case _Estado.listo:
        return GridView.builder(
          padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.lg),
          itemCount: _productos.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            mainAxisSpacing: AppSpacing.lg,
            crossAxisSpacing: AppSpacing.md,
            childAspectRatio: 0.6,
          ),
          itemBuilder: (context, index) {
            final producto = _productos[index];
            return ProductCard(
              producto: producto,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => ProductoDetallePage(producto: producto)),
              ),
            );
          },
        );
    }
  }
}
