import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../shared/widgets/async_state_message.dart';
import '../../shared/widgets/sucursal_card.dart';
import 'models/ciudad.dart';
import 'models/sucursal.dart';
import 'sucursal_detalle_page.dart';
import 'sucursales_service.dart';

enum _Estado { cargando, listo, vacio, error }

/// CU07 -- Consultar sucursales. Público: no requiere sesión. Accesible
/// desde el tab "Explorar" (icono en el AppBar del catálogo general).
///
/// El filtro por ciudad usa `ciudad_id` en el backend (CU07 ya lo soporta),
/// no un filtro local en Dart -- cada cambio de ciudad vuelve a consultar
/// FastAPI.
class SucursalesPage extends StatefulWidget {
  const SucursalesPage({super.key});

  @override
  State<SucursalesPage> createState() => _SucursalesPageState();
}

class _SucursalesPageState extends State<SucursalesPage> {
  final _sucursalesService = SucursalesService();

  _Estado _estado = _Estado.cargando;
  List<Sucursal> _sucursales = [];
  List<Ciudad> _ciudades = [];
  int? _ciudadSeleccionada;

  @override
  void initState() {
    super.initState();
    _cargarCiudades();
    _cargarSucursales();
  }

  Future<void> _cargarCiudades() async {
    try {
      final ciudades = await _sucursalesService.listarCiudades();
      if (!mounted) return;
      setState(() => _ciudades = ciudades);
    } catch (_) {
      // Si fallan las ciudades, la lista de sucursales sigue funcionando
      // sin filtro -- no se rompe la pantalla por esto.
    }
  }

  Future<void> _cargarSucursales() async {
    setState(() => _estado = _Estado.cargando);
    try {
      final sucursales = await _sucursalesService.listarSucursales(
        ciudadId: _ciudadSeleccionada,
      );
      if (!mounted) return;
      setState(() {
        _sucursales = sucursales;
        _estado = sucursales.isEmpty ? _Estado.vacio : _Estado.listo;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  void _seleccionarCiudad(int? ciudadId) {
    if (_ciudadSeleccionada == ciudadId) return;
    setState(() => _ciudadSeleccionada = ciudadId);
    _cargarSucursales();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sucursales')),
      body: SafeArea(
        child: Column(
          children: [
            if (_ciudades.isNotEmpty)
              SizedBox(
                height: 44,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
                  children: [
                    _CiudadChip(
                      label: 'Todas',
                      selected: _ciudadSeleccionada == null,
                      onTap: () => _seleccionarCiudad(null),
                    ),
                    for (final ciudad in _ciudades) ...[
                      const SizedBox(width: AppSpacing.sm),
                      _CiudadChip(
                        label: ciudad.nombre,
                        selected: _ciudadSeleccionada == ciudad.id,
                        onTap: () => _seleccionarCiudad(ciudad.id),
                      ),
                    ],
                  ],
                ),
              ),
            const SizedBox(height: AppSpacing.md),
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
          child: AsyncStateMessage(
            message: 'No se pudieron cargar las sucursales.',
            onRetry: _cargarSucursales,
          ),
        );
      case _Estado.vacio:
        return const Center(
          child: AsyncStateMessage(
            message: 'No hay sucursales disponibles.',
            icon: Icons.storefront_outlined,
          ),
        );
      case _Estado.listo:
        return ListView.separated(
          padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.lg),
          itemCount: _sucursales.length,
          separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.md),
          itemBuilder: (context, index) {
            final sucursal = _sucursales[index];
            return SucursalCard(
              sucursal: sucursal,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => SucursalDetallePage(sucursal: sucursal)),
              ),
            );
          },
        );
    }
  }
}

class _CiudadChip extends StatelessWidget {
  const _CiudadChip({required this.label, required this.selected, required this.onTap});

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: selected ? AppColors.burgundy : AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: Text(
          label,
          style: AppTextStyles.bodyMuted.copyWith(
            color: selected ? AppColors.cream : AppColors.charcoal,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}
