import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../catalogo/catalogo_page.dart';
import '../catalogo/catalogo_service.dart';
import '../catalogo/colecciones_page.dart';
import '../catalogo/models/categoria.dart';
import '../catalogo/models/coleccion.dart';
import '../catalogo/models/producto.dart';
import '../catalogo/producto_detalle_page.dart';
import 'widgets/category_scroller.dart';
import 'widgets/collections_section.dart';
import 'widgets/hero_section.dart';
import 'widgets/product_section.dart';

/// Home pública de FashionStore Mobile. No requiere sesión: header, bloque
/// editorial, categorías y productos son todos datos/endpoints públicos de
/// CU07/CU10/CU11. El login se pide más adelante, solo cuando el Cliente
/// intente una acción personal (reservar, comprar, ver su perfil).
class HomePage extends StatefulWidget {
  const HomePage({super.key, this.onAbrirCarrito, this.onAbrirPerfil});

  final VoidCallback? onAbrirCarrito;
  final VoidCallback? onAbrirPerfil;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _catalogoService = CatalogoService();

  void _abrirCatalogo({int? categoriaId, String titulo = 'Explorar'}) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => CatalogoPage(categoriaId: categoriaId, titulo: titulo),
      ),
    );
  }

  void _abrirColeccion(Coleccion coleccion) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => CatalogoPage(coleccion: coleccion)),
    );
  }

  void _abrirColecciones() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const ColeccionesPage()),
    );
  }

  void _abrirProducto(Producto producto) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ProductoDetallePage(producto: producto)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        bottom: false,
        child: CustomScrollView(
          slivers: [
            SliverToBoxAdapter(child: _Header(
              onBuscar: () => _abrirCatalogo(),
              onCarrito: widget.onAbrirCarrito,
              onPerfil: widget.onAbrirPerfil,
            )),
            SliverToBoxAdapter(
              child: HeroSection(
                catalogoService: _catalogoService,
                onExplorarCatalogo: () => _abrirCatalogo(),
                onExplorarColeccion: _abrirColeccion,
              ),
            ),
            SliverToBoxAdapter(
              child: CategoryScroller(
                catalogoService: _catalogoService,
                onCategoriaSeleccionada: (Categoria categoria) =>
                    _abrirCatalogo(categoriaId: categoria.id, titulo: categoria.nombre),
              ),
            ),
            const SliverToBoxAdapter(child: SizedBox(height: AppSpacing.xl)),
            SliverToBoxAdapter(
              child: CollectionsSection(
                catalogoService: _catalogoService,
                onVerTodas: _abrirColecciones,
                onColeccionSeleccionada: _abrirColeccion,
              ),
            ),
            const SliverToBoxAdapter(child: SizedBox(height: AppSpacing.xl)),
            SliverToBoxAdapter(
              child: ProductSection(
                catalogoService: _catalogoService,
                onVerTodos: () => _abrirCatalogo(),
                onProductoSeleccionado: _abrirProducto,
              ),
            ),
            const SliverToBoxAdapter(child: SizedBox(height: AppSpacing.xxl)),
          ],
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.onBuscar, this.onCarrito, this.onPerfil});

  final VoidCallback onBuscar;
  final VoidCallback? onCarrito;
  final VoidCallback? onPerfil;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.md, AppSpacing.sm, AppSpacing.sm),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.divider)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 6,
                  height: 6,
                  margin: const EdgeInsets.only(right: AppSpacing.sm),
                  decoration: const BoxDecoration(color: AppColors.burgundy, shape: BoxShape.circle),
                ),
                const Flexible(child: Text('FASHIONSTORE', style: AppTextStyles.brand)),
              ],
            ),
          ),
          IconButton(
            onPressed: onBuscar,
            icon: const Icon(Icons.search, color: AppColors.charcoal),
            tooltip: 'Buscar',
          ),
          IconButton(
            onPressed: onCarrito,
            icon: const Icon(Icons.shopping_bag_outlined, color: AppColors.charcoal),
            tooltip: 'Carrito',
          ),
          IconButton(
            onPressed: onPerfil,
            icon: const Icon(Icons.person_outline, color: AppColors.charcoal),
            tooltip: 'Perfil',
          ),
        ],
      ),
    );
  }
}
