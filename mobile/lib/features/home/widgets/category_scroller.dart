import 'package:flutter/material.dart';

import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/async_state_message.dart';
import '../../../shared/widgets/category_item.dart';
import '../../../shared/widgets/section_header.dart';
import '../../catalogo/catalogo_service.dart';
import '../../catalogo/models/categoria.dart';

enum _Estado { cargando, listo, vacio, error }

/// Scroll horizontal de categorías reales (CU11 -- /catalogo/categorias).
/// No hardcodea "Mujer/Hombre/Accesorios": muestra exactamente lo que
/// devuelve el backend, igual que lo hace Angular.
class CategoryScroller extends StatefulWidget {
  const CategoryScroller({
    super.key,
    required this.catalogoService,
    required this.onCategoriaSeleccionada,
  });

  final CatalogoService catalogoService;
  final void Function(Categoria categoria) onCategoriaSeleccionada;

  @override
  State<CategoryScroller> createState() => _CategoryScrollerState();
}

class _CategoryScrollerState extends State<CategoryScroller> {
  _Estado _estado = _Estado.cargando;
  List<Categoria> _categorias = [];

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _estado = _Estado.cargando);
    try {
      final categorias = await widget.catalogoService.listarCategorias();
      if (!mounted) return;
      setState(() {
        _categorias = categorias;
        _estado = categorias.isEmpty ? _Estado.vacio : _Estado.listo;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Sin categorías reales: no se muestra la sección (nunca se inventa una).
    if (_estado == _Estado.vacio) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SectionHeader(title: 'Categorías'),
        const SizedBox(height: AppSpacing.md),
        if (_estado == _Estado.cargando)
          const SizedBox(
            height: 96,
            child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
          )
        else if (_estado == _Estado.error)
          AsyncStateMessage(message: 'No se pudieron cargar las categorías.', onRetry: _cargar)
        else
          SizedBox(
            height: 104,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              itemCount: _categorias.length,
              separatorBuilder: (_, _) => const SizedBox(width: AppSpacing.md),
              itemBuilder: (context, index) {
                final categoria = _categorias[index];
                return CategoryItem(
                  categoria: categoria,
                  onTap: () => widget.onCategoriaSeleccionada(categoria),
                );
              },
            ),
          ),
      ],
    );
  }
}
