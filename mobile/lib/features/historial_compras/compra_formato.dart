/// Formato de fecha/hora y etiquetas de una compra -- sin depender de `intl`
/// (no está entre las dependencias del proyecto, ver pubspec.yaml), mismo
/// criterio minimalista que reservas/reserva_formato.dart. Etiquetas y
/// formato de fecha calcados 1:1 de los mismos helpers en Angular (ver
/// frontend/web/.../historial-compras.ts y comprobante-detalle.ts) -- para
/// que "Mis compras" se vea idéntico entre web y móvil.
library;

/// Fecha corta (sin hora) -- igual que `fecha()` en
/// features/cliente/historial-compras/historial-compras.ts, usada en las
/// tarjetas de la lista.
String formatearFechaCompra(String fechaIso) {
  final fecha = DateTime.tryParse(fechaIso)?.toLocal();
  if (fecha == null) return fechaIso;

  final dia = fecha.day.toString().padLeft(2, '0');
  final mes = fecha.month.toString().padLeft(2, '0');
  return '$dia/$mes/${fecha.year}';
}

/// Fecha con hora -- igual que `fecha()` en
/// features/comprobantes/comprobante-detalle/comprobante-detalle.ts, usada
/// en el detalle de una compra.
String formatearFechaHoraCompra(String fechaIso) {
  final fecha = DateTime.tryParse(fechaIso)?.toLocal();
  if (fecha == null) return fechaIso;

  final dia = fecha.day.toString().padLeft(2, '0');
  final mes = fecha.month.toString().padLeft(2, '0');
  final hora = fecha.hour.toString().padLeft(2, '0');
  final minuto = fecha.minute.toString().padLeft(2, '0');
  return '$dia/$mes/${fecha.year} $hora:$minuto';
}

/// "YYYY-MM-DD" -- formato que espera FastAPI en `desde`/`hasta`
/// (`date` de Python), igual que el `<input type="date">` de Angular.
String formatearFechaParaApi(DateTime fecha) {
  final anio = fecha.year.toString().padLeft(4, '0');
  final mes = fecha.month.toString().padLeft(2, '0');
  final dia = fecha.day.toString().padLeft(2, '0');
  return '$anio-$mes-$dia';
}

/// Mismos 2 valores reales del backend (`Venta.tipo`) -- igual que
/// `etiquetaTipo()` en historial-compras.ts / comprobante-detalle.html.
String etiquetaTipoVenta(String tipo) => tipo == 'DIGITAL' ? 'Digital' : 'Presencial';

/// Mismos 4 valores reales del backend (`Pago.proveedor`) -- igual que
/// `etiquetaMetodo()` en historial-compras.ts / comprobante-detalle.ts.
String etiquetaMetodoPago(String metodo) {
  switch (metodo) {
    case 'STRIPE':
      return 'Stripe';
    case 'EFECTIVO':
      return 'Efectivo';
    case 'TARJETA':
      return 'Tarjeta';
    case 'QR':
      return 'QR';
    default:
      return metodo;
  }
}
