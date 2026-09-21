import 'package:flutter/material.dart';

import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/async_state_message.dart';
import '../../../shared/widgets/product_card.dart';
import '../../../shared/widgets/section_header.dart';
import '../../catalogo/catalogo_service.dart';
import '../../catalogo/models/producto.dart';

const _maxHomeProductos = 6;

enum _Estado { cargando, listo, vacio, error }

/// Vista previa del catálogo en la Home (CU11 -- /catalogo/productos).
/// Título "Explorar productos": es el mismo nombre real que ya usa
/// Angular para esta sección (no "Destacados para ti" -- no existe una
/// selección personalizada real que lo respalde).
class ProductSection extends StatefulWidget {
  const ProductSection({
    super.key,
    required this.catalogoService,
    required this.onVerTodos,
    required this.onProductoSeleccionado,
  });

  final CatalogoService catalogoService;
  final VoidCallback onVerTodos;
  final void Function(Producto producto) onProductoSeleccionado;

  @override
  State<ProductSection> createState() => _ProductSectionState();
}

class _ProductSectionState extends State<ProductSection> {
  _Estado _estado = _Estado.cargando;
  List<Producto> _productos = [];

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _estado = _Estado.cargando);
    try {
      final productos = await widget.catalogoService.listarProductos();
      if (!mounted) return;
      setState(() {
        _productos = productos.take(_maxHomeProductos).toList();
        _estado = _productos.isEmpty ? _Estado.vacio : _Estado.listo;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SectionHeader(
          title: 'Explorar productos',
          actionLabel: _estado == _Estado.listo ? 'Ver todos' : null,
          onAction: widget.onVerTodos,
        ),
        const SizedBox(height: AppSpacing.md),
        if (_estado == _Estado.cargando)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: AppSpacing.xl),
            child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
          )
        else if (_estado == _Estado.error)
          AsyncStateMessage(message: 'No se pudieron cargar los productos.', onRetry: _cargar)
        else if (_estado == _Estado.vacio)
          const AsyncStateMessage(
            message: 'No hay prendas publicadas todavía.',
            icon: Icons.checkroom_outlined,
          )
        else
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
            child: GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
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
                  onTap: () => widget.onProductoSeleccionado(producto),
                );
              },
            ),
          ),
      ],
    );
  }
}
