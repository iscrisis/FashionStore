import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_radius.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../shared/widgets/primary_button.dart';
import '../../catalogo/catalogo_service.dart';
import '../../catalogo/models/coleccion.dart';

/// Bloque editorial principal de la Home. Sin fotografías: el efecto
/// premium se logra con degradado burdeos/rojo, formas geométricas y
/// tipografía -- nunca con imágenes decorativas ni frases comerciales
/// inventadas.
///
/// Si el Administrador marcó una colección como destacada (CU10 --
/// /colecciones/destacada), se muestra su nombre real (resuelto cruzando el
/// id contra /catalogo/colecciones, que sí trae nombre) y un CTA hacia ella.
/// Si no hay ninguna marcada (estado real actual), se muestra únicamente la
/// marca y un CTA neutral hacia el catálogo -- nunca un texto de campaña
/// inventado.
class HeroSection extends StatefulWidget {
  const HeroSection({
    super.key,
    required this.catalogoService,
    required this.onExplorarCatalogo,
    required this.onExplorarColeccion,
  });

  final CatalogoService catalogoService;
  final VoidCallback onExplorarCatalogo;
  final void Function(Coleccion coleccion) onExplorarColeccion;

  @override
  State<HeroSection> createState() => _HeroSectionState();
}

class _HeroSectionState extends State<HeroSection> {
  Coleccion? _destacada;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    try {
      final destacada = await widget.catalogoService.obtenerColeccionDestacada();
      if (destacada == null || !mounted) return;
      final colecciones = await widget.catalogoService.listarColecciones();
      final match = colecciones.where((c) => c.id == destacada.id);
      if (match.isNotEmpty && mounted) {
        setState(() => _destacada = match.first);
      }
    } catch (_) {
      // Silencioso a propósito: si falla, el hero simplemente se queda en
      // su estado neutral -- nunca rompe la Home por esto.
    }
  }

  @override
  Widget build(BuildContext context) {
    final destacada = _destacada;

    return Padding(
      padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, AppSpacing.lg),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppRadius.lg),
        child: SizedBox(
          height: 200,
          child: Stack(
            fit: StackFit.expand,
            children: [
              const DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [AppColors.burgundy, AppColors.burgundy, AppColors.red],
                    stops: [0, 0.55, 1],
                  ),
                ),
              ),
              Positioned(
                right: -36,
                top: -36,
                child: _GeometricCircle(size: 150, color: AppColors.gold.withValues(alpha: 0.16)),
              ),
              Positioned(
                right: 24,
                bottom: -60,
                child: _GeometricCircle(size: 130, color: AppColors.cream.withValues(alpha: 0.08)),
              ),
              Padding(
                padding: const EdgeInsets.all(AppSpacing.lg),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Acento dorado reducido a una línea -- sin texto
                        // "COLECCIÓN DESTACADA" (información interna, no
                        // le aporta nada al Cliente). Con destacada real
                        // se muestra directamente su nombre; sin ella,
                        // solo la marca.
                        Container(width: 28, height: 2, color: AppColors.gold),
                        const SizedBox(height: AppSpacing.sm),
                        Text(
                          destacada?.nombre ?? 'FASHIONSTORE',
                          style: AppTextStyles.display.copyWith(color: AppColors.cream, fontSize: 26),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                    PrimaryButton(
                      // "NUEVA COLECCIÓN" solo cuando hay una colección destacada
                      // REAL (CU10) a la que llevar -- si no existe ninguna, se
                      // mantiene un CTA neutral hacia el catálogo, nunca se
                      // promete una colección que no existe.
                      label: destacada != null ? 'NUEVA COLECCIÓN' : 'Explorar catálogo',
                      variant: PrimaryButtonVariant.outline,
                      onPressed: () {
                        if (destacada != null) {
                          widget.onExplorarColeccion(destacada);
                        } else {
                          widget.onExplorarCatalogo();
                        }
                      },
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _GeometricCircle extends StatelessWidget {
  const _GeometricCircle({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(shape: BoxShape.circle, color: color),
    );
  }
}
