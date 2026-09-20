import 'package:flutter/material.dart';

import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/async_state_message.dart';
import '../../../shared/widgets/collection_card.dart';
import '../../../shared/widgets/section_header.dart';
import '../../catalogo/catalogo_service.dart';
import '../../catalogo/models/coleccion.dart';

enum _Estado { cargando, listo, vacio, error }

/// Scroll horizontal de colecciones reales (CU11 -- /catalogo/colecciones).
/// Una colección agrupa productos de distintas categorías (p. ej. una
/// colección puede tener chaquetas, blusas y accesorios a la vez) -- por
/// eso es una sección propia, distinta de Categorías. Sin carrusel
/// automático, sin dots: solo `ListView` horizontal nativo.
class CollectionsSection extends StatefulWidget {
  const CollectionsSection({
    super.key,
    required this.catalogoService,
    required this.onVerTodas,
    required this.onColeccionSeleccionada,
  });

  final CatalogoService catalogoService;
  final VoidCallback onVerTodas;
  final void Function(Coleccion coleccion) onColeccionSeleccionada;

  @override
  State<CollectionsSection> createState() => _CollectionsSectionState();
}

class _CollectionsSectionState extends State<CollectionsSection> {
  _Estado _estado = _Estado.cargando;
  List<Coleccion> _colecciones = [];

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _estado = _Estado.cargando);
    try {
      final colecciones = await widget.catalogoService.listarColecciones();
      if (!mounted) return;
      setState(() {
        _colecciones = colecciones;
        _estado = colecciones.isEmpty ? _Estado.vacio : _Estado.listo;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Sin colecciones reales: no se muestra la sección (nunca se inventa una).
    if (_estado == _Estado.vacio) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SectionHeader(
          title: 'Colecciones',
          actionLabel: _estado == _Estado.listo ? 'Ver todas' : null,
          onAction: widget.onVerTodas,
        ),
        const SizedBox(height: AppSpacing.md),
        if (_estado == _Estado.cargando)
          const SizedBox(
            height: 128,
            child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
          )
        else if (_estado == _Estado.error)
          AsyncStateMessage(message: 'No se pudieron cargar las colecciones.', onRetry: _cargar)
        else
          SizedBox(
            height: 128,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              itemCount: _colecciones.length,
              separatorBuilder: (_, _) => const SizedBox(width: AppSpacing.md),
              itemBuilder: (context, index) {
                final coleccion = _colecciones[index];
                return SizedBox(
                  width: 168,
                  child: CollectionCard(
                    coleccion: coleccion,
                    onTap: () => widget.onColeccionSeleccionada(coleccion),
                  ),
                );
              },
            ),
          ),
      ],
    );
  }
}
