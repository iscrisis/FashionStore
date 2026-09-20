import 'package:flutter/material.dart';

import '../../core/theme/app_spacing.dart';
import '../../shared/widgets/async_state_message.dart';
import '../../shared/widgets/collection_card.dart';
import 'catalogo_page.dart';
import 'catalogo_service.dart';
import 'models/coleccion.dart';

enum _Estado { cargando, listo, vacio, error }

/// "Ver todas" de la sección Colecciones -- lista completa de colecciones
/// reales (CU11 -- /catalogo/colecciones), sin inventar ninguna. Reutiliza
/// [CollectionCard] (mismo componente que el scroll de la Home) y
/// [CatalogoPage] para mostrar los productos al tocar una.
class ColeccionesPage extends StatefulWidget {
  const ColeccionesPage({super.key});

  @override
  State<ColeccionesPage> createState() => _ColeccionesPageState();
}

class _ColeccionesPageState extends State<ColeccionesPage> {
  final _catalogoService = CatalogoService();
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
      final colecciones = await _catalogoService.listarColecciones();
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
    return Scaffold(
      appBar: AppBar(title: const Text('Colecciones')),
      body: SafeArea(child: _buildBody()),
    );
  }

  Widget _buildBody() {
    switch (_estado) {
      case _Estado.cargando:
        return const Center(child: CircularProgressIndicator(strokeWidth: 2));
      case _Estado.error:
        return Center(
          child: AsyncStateMessage(message: 'No se pudieron cargar las colecciones.', onRetry: _cargar),
        );
      case _Estado.vacio:
        return const Center(
          child: AsyncStateMessage(
            message: 'No hay colecciones publicadas todavía.',
            icon: Icons.style_outlined,
          ),
        );
      case _Estado.listo:
        return GridView.builder(
          padding: const EdgeInsets.all(AppSpacing.lg),
          itemCount: _colecciones.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            mainAxisSpacing: AppSpacing.md,
            crossAxisSpacing: AppSpacing.md,
            childAspectRatio: 1.2,
          ),
          itemBuilder: (context, index) {
            final coleccion = _colecciones[index];
            return CollectionCard(
              coleccion: coleccion,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => CatalogoPage(coleccion: coleccion)),
              ),
            );
          },
        );
    }
  }
}
