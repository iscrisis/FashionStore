import 'package:flutter/material.dart';

/// Ajuste inicial "inteligente" del overlay según la CATEGORÍA del
/// producto (Blusas, Vestidos, Pantalones, ...) -- NO es detección
/// corporal ni nada calculado a partir del video de la cámara: es una
/// tabla estática, la misma para todos los Clientes, que solo decide en
/// qué zona del encuadre y a qué escala aparece la prenda apenas se abre
/// el vestidor. El Cliente sigue pudiendo mover/escalar manualmente desde
/// ahí (ver `OverlayControles`); esto solo evita que TODAS las prendas
/// arranquen con el mismo tamaño/posición sin importar si es una blusa
/// (zona superior) o un pantalón (zona inferior).
class ConfiguracionPrendaCategoria {
  const ConfiguracionPrendaCategoria({
    required this.alineacion,
    required this.widthFactor,
    required this.heightFactor,
  });

  /// Punto del encuadre donde se centra la prenda al abrir el vestidor.
  /// Y negativo = zona superior del cuerpo (torso/pecho), Y positivo =
  /// zona inferior (piernas).
  final Alignment alineacion;

  /// Proporción del ancho/alto disponible que ocupa la prenda -- se
  /// combina con `BoxFit.contain` en `PrendaOverlay`, así que la prenda
  /// nunca se deforma, esto solo fija el espacio máximo inicial.
  final double widthFactor;
  final double heightFactor;
}

const _configuracionesPorCategoria = <String, ConfiguracionPrendaCategoria>{
  // Prendas de torso (zona superior) -- la mayoría del catálogo actual.
  'blusas': ConfiguracionPrendaCategoria(
    alineacion: Alignment(0, -0.18),
    widthFactor: 0.5,
    heightFactor: 0.5,
  ),
  'camisas': ConfiguracionPrendaCategoria(
    alineacion: Alignment(0, -0.18),
    widthFactor: 0.5,
    heightFactor: 0.5,
  ),
  'chaquetas': ConfiguracionPrendaCategoria(
    alineacion: Alignment(0, -0.15),
    widthFactor: 0.56,
    heightFactor: 0.55,
  ),
  'sueteres': ConfiguracionPrendaCategoria(
    alineacion: Alignment(0, -0.18),
    widthFactor: 0.52,
    heightFactor: 0.5,
  ),

  // Prendas de cuerpo completo -- ocupan más alto, centradas.
  'vestidos': ConfiguracionPrendaCategoria(
    alineacion: Alignment(0, 0.02),
    widthFactor: 0.5,
    heightFactor: 0.72,
  ),

  // Prendas de zona inferior (piernas) -- se ubican más abajo.
  'pantalones': ConfiguracionPrendaCategoria(
    alineacion: Alignment(0, 0.3),
    widthFactor: 0.42,
    heightFactor: 0.42,
  ),
  'faldas': ConfiguracionPrendaCategoria(
    alineacion: Alignment(0, 0.26),
    widthFactor: 0.44,
    heightFactor: 0.38,
  ),
};

/// Configuración genérica para cualquier categoría todavía no mapeada
/// arriba (por ejemplo una nueva categoría que el Administrador cree en
/// el catálogo) -- misma zona de torso que "Blusas", el caso más común.
const _configuracionPorDefecto = ConfiguracionPrendaCategoria(
  alineacion: Alignment(0, -0.15),
  widthFactor: 0.5,
  heightFactor: 0.5,
);

/// Busca la configuración por nombre de categoría, sin distinguir
/// mayúsculas/acentos exactos (`categoriaNombre` viene tal cual la
/// escribió el Administrador en el catálogo, ver CU08/CU09 del backend).
ConfiguracionPrendaCategoria configuracionParaCategoria(String categoriaNombre) {
  final clave = categoriaNombre.trim().toLowerCase();
  return _configuracionesPorCategoria[clave] ?? _configuracionPorDefecto;
}
