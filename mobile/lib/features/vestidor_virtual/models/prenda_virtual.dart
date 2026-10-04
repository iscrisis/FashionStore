/// Datos de la prenda ya elegida en el detalle de producto (talla/color)
/// que necesita el vestidor virtual -- NO es un modelo de red (no refleja
/// ningún `*Out` de FastAPI): se arma en el propio Flutter a partir de la
/// selección que ya hizo el Cliente en `ProductoDetallePage`, sin golpear
/// ningún endpoint nuevo.
///
/// Desacoplado a propósito de la imagen normal del catálogo
/// (`imagenCatalogoUrl`, la MISMA `Producto.imagenPrincipalUrl` servida por
/// el backend): esta clase la reutiliza SOLO para el encabezado ("qué
/// producto estoy probando"), nunca para el overlay -- el overlay es
/// SIEMPRE un recurso local en `assets/vestidor/`, nunca una URL de red,
/// así que un producto sin PNG preparado simplemente no rompe la galería
/// del catálogo ni viceversa.
class PrendaVirtual {
  const PrendaVirtual({
    required this.productoId,
    required this.nombre,
    required this.categoriaNombre,
    required this.tallaNombre,
    required this.colorNombre,
    this.imagenCatalogoUrl,
    this.imagenVirtualAsset,
  });

  final int productoId;
  final String nombre;
  final String categoriaNombre;

  // Talla/color se reciben tal cual los eligió el Cliente en
  // `ProductoDetallePage` -- siguen siendo información de la VARIANTE del
  // producto (igual que en el resto de la app: carrito, reservas), el
  // vestidor virtual solo la muestra como contexto secundario, nunca la
  // reinterpreta ni la vuelve a validar.
  final String tallaNombre;
  final String colorNombre;

  /// URL ya resuelta (ver `MediaUrl.resolve`) de la imagen NORMAL del
  /// catálogo -- solo para la miniatura del encabezado, `null` si el
  /// producto no tiene imagen principal. Completamente independiente del
  /// PNG del overlay.
  final String? imagenCatalogoUrl;

  /// Ruta explícita del PNG transparente a superponer. Si es `null`
  /// (caso normal del MVP, todavía sin catálogo completo de imágenes por
  /// producto) se usa la convención `overlayAssetPath` de abajo;
  /// `PrendaOverlay` igual sabe mostrar un estado "no disponible" si el
  /// archivo no existe, sin exponer errores técnicos.
  final String? imagenVirtualAsset;

  /// Convención de nombre de archivo para preparar `assets/vestidor/`:
  /// un PNG transparente por producto, nombrado con su id de catálogo.
  String get overlayAssetPath => imagenVirtualAsset ?? 'assets/vestidor/producto_$productoId.png';
}
