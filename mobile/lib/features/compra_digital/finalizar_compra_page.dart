import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/storage/token_storage.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/media_url.dart';
import '../auth/auth_service.dart';
import '../auth/login_page.dart';
import '../auth/models/usuario_sesion.dart';
import '../pago_electronico/pago_page.dart';
import '../sucursales/models/ciudad.dart';
import '../sucursales/sucursales_service.dart';
import 'compra_digital_service.dart';
import 'models/compra_digital.dart';

enum _SesionEstado { verificando, sinSesion, lista }

/// CU22 -- Realizar compra digital (Cliente). Se llega aquí SOLO desde
/// "CONTINUAR COMPRA" en el carrito (CU21, ver mi_carrito_page.dart) -- por
/// eso ya hay sesión garantizada en la práctica, pero esta pantalla igual
/// revalida por sí misma (mismo criterio defensivo que MisReservasPage/
/// MiCarritoPage) en vez de asumirlo.
///
/// UNA sola pantalla con 3 secciones (Productos / Ubicación / Resumen), no
/// un asistente de varios pasos: los productos y el total SIEMPRE son los
/// que ya trae `GET /compra-digital/resumen` (las prendas que el Cliente
/// marcó `seleccionado` en su carrito, CU21) -- nunca una lista nueva ni una
/// cantidad inventada aquí. Ciudad/sucursal se eligen AQUÍ, nunca en el
/// carrito ni al agregar un producto -- a diferencia de CU17 (Reservar), que
/// vive dentro del detalle del producto, este flujo nace en el carrito y no
/// se parece a una reserva: no pide fecha ni horario, solo dónde retirar.
///
/// Al confirmar, la `Venta` queda SIEMPRE en PENDIENTE_PAGO (ver
/// Models/venta.py -- CU22 nunca la crea ya pagada), así que esta pantalla
/// NO muestra ningún mensaje de "compra realizada": navega directo a
/// [PagoPage] (CU23), con la misma `VentaOut` real que acaba de devolver el
/// backend. Comprobante (CU31) sigue fuera de este alcance.
class FinalizarCompraPage extends StatefulWidget {
  const FinalizarCompraPage({super.key});

  @override
  State<FinalizarCompraPage> createState() => _FinalizarCompraPageState();
}

class _FinalizarCompraPageState extends State<FinalizarCompraPage> {
  final _authService = AuthService();
  final _service = CompraDigitalService();
  final _sucursalesService = SucursalesService();

  _SesionEstado _sesionEstado = _SesionEstado.verificando;
  String? _token;

  bool _cargandoResumen = true;
  String? _errorResumen;
  ResumenCompraOut? _resumen;

  // La ciudad nace en null a propósito (mismo criterio que CU12/CU17 en el
  // detalle de producto): nunca se autoselecciona la primera de la lista.
  List<Ciudad> _ciudades = [];
  bool _cargandoCiudades = true;
  int? _ciudadSeleccionadaId;

  List<SucursalCompraOut> _sucursales = [];
  bool _cargandoSucursales = false;
  bool _sucursalesConsultadas = false;
  String? _errorSucursales;
  int? _sucursalSeleccionadaId;

  bool _confirmando = false;

  @override
  void initState() {
    super.initState();
    _iniciar();
  }

  Future<void> _iniciar() async {
    final sesion = await _authService.sesionGuardada();
    if (!mounted) return;
    if (sesion == null) {
      setState(() => _sesionEstado = _SesionEstado.sinSesion);
      return;
    }
    final token = await TokenStorage.getToken();
    if (!mounted) return;
    if (token == null) {
      setState(() => _sesionEstado = _SesionEstado.sinSesion);
      return;
    }
    setState(() {
      _token = token;
      _sesionEstado = _SesionEstado.lista;
    });
    _cargarResumen();
    _cargarCiudades();
  }

  void _onLoginExitoso(UsuarioSesion usuario) {
    _iniciar();
  }

  Future<void> _cargarResumen() async {
    final token = _token;
    if (token == null) return;
    setState(() {
      _cargandoResumen = true;
      _errorResumen = null;
    });
    try {
      final resumen = await _service.obtenerResumen(token: token);
      if (!mounted) return;
      setState(() {
        _resumen = resumen;
        _cargandoResumen = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _cargandoResumen = false;
        _errorResumen = _mensajeAmigable(e);
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cargandoResumen = false;
        _errorResumen = 'No se pudo cargar el resumen de tu compra. Inténtalo nuevamente.';
      });
    }
  }

  Future<void> _cargarCiudades() async {
    try {
      final ciudades = await _sucursalesService.listarCiudades();
      if (!mounted) return;
      setState(() {
        _ciudades = ciudades;
        _cargandoCiudades = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _cargandoCiudades = false);
    }
  }

  void _seleccionarCiudad(int? ciudadId) {
    setState(() {
      _ciudadSeleccionadaId = ciudadId;
      _sucursales = [];
      _sucursalesConsultadas = false;
      _errorSucursales = null;
      _sucursalSeleccionadaId = null;
    });
    if (ciudadId != null) {
      _cargarSucursales(ciudadId);
    }
  }

  Future<void> _cargarSucursales(int ciudadId) async {
    final token = _token;
    if (token == null) return;
    setState(() {
      _cargandoSucursales = true;
      _errorSucursales = null;
    });
    try {
      final sucursales = await _service.listarSucursales(ciudadId: ciudadId, token: token);
      if (!mounted) return;
      setState(() {
        _sucursales = sucursales;
        _cargandoSucursales = false;
        _sucursalesConsultadas = true;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _cargandoSucursales = false;
        _sucursalesConsultadas = true;
        _errorSucursales = _mensajeAmigable(e);
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cargandoSucursales = false;
        _sucursalesConsultadas = true;
        _errorSucursales = 'No se pudo consultar las sucursales de esa ciudad.';
      });
    }
  }

  void _seleccionarSucursal(SucursalCompraOut sucursal) {
    if (!sucursal.disponibleParaCompra || _confirmando) return;
    setState(() => _sucursalSeleccionadaId = sucursal.id);
  }

  bool get _puedeConfirmar => _sucursalSeleccionadaId != null && !_confirmando && _resumen != null;

  Future<void> _confirmar() async {
    final token = _token;
    final sucursalId = _sucursalSeleccionadaId;
    if (token == null || sucursalId == null || !_puedeConfirmar) return;

    setState(() => _confirmando = true);
    try {
      final venta = await _service.confirmar(sucursalId: sucursalId, token: token);
      if (!mounted) return;

      // `venta.estado` viene PENDIENTE_PAGO -- se navega directo a CU23
      // (PagoPage) con esa misma Venta real, nunca se muestra un mensaje de
      // compra terminada aquí. `pushReplacement`: esta pantalla de ubicación
      // ya no tiene sentido una vez creada la venta -- "volver" desde el
      // pago debe caer directo en el carrito (CU21), no en este formulario.
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => PagoPage(venta: venta)),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _confirmando = false;
        // La sucursal pudo dejar de tener disponibilidad justo ahora --
        // se vuelve a elegir en vez de reintentar a ciegas contra la misma
        // (mismo criterio que ya usa Angular, ver finalizar-compra.ts).
        _sucursalSeleccionadaId = null;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_mensajeAmigable(e)), backgroundColor: AppColors.red),
      );
      final ciudadId = _ciudadSeleccionadaId;
      if (ciudadId != null) _cargarSucursales(ciudadId);
    } catch (_) {
      if (!mounted) return;
      setState(() => _confirmando = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No se pudo completar la compra. Inténtalo nuevamente.'),
          backgroundColor: AppColors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_sesionEstado == _SesionEstado.sinSesion) {
      return LoginPage(onLoginExitoso: _onLoginExitoso);
    }
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(title: const Text('Compra')),
      body: SafeArea(child: _buildBody()),
    );
  }

  Widget _buildBody() {
    if (_sesionEstado == _SesionEstado.verificando || _cargandoResumen) {
      return const Center(child: CircularProgressIndicator(strokeWidth: 2));
    }
    final error = _errorResumen;
    if (error != null) {
      return _ErrorConAccion(
        mensaje: error,
        etiquetaAccion: 'Volver al carrito',
        onAccion: () => Navigator.of(context).pop(),
      );
    }
    final resumen = _resumen;
    if (resumen == null) {
      return const SizedBox.shrink();
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Productos', style: AppTextStyles.sectionTitle.copyWith(fontSize: 15)),
          const SizedBox(height: AppSpacing.sm),
          for (final linea in resumen.items)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: _LineaCompraCard(linea: linea),
            ),
          const SizedBox(height: AppSpacing.xs),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Subtotal', style: AppTextStyles.bodyMuted),
              Text(
                'Bs ${resumen.total.toStringAsFixed(2)}',
                style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xl),
          Text('Ubicación', style: AppTextStyles.sectionTitle.copyWith(fontSize: 15)),
          const SizedBox(height: AppSpacing.sm),
          _SelectorCiudadCompra(
            ciudades: _ciudades,
            ciudadSeleccionadaId: _ciudadSeleccionadaId,
            cargando: _cargandoCiudades,
            onChanged: _seleccionarCiudad,
          ),
          const SizedBox(height: AppSpacing.md),
          _buildSucursales(),
          const SizedBox(height: AppSpacing.xl),
          Text('Resumen', style: AppTextStyles.sectionTitle.copyWith(fontSize: 15)),
          const SizedBox(height: AppSpacing.sm),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Total', style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600)),
                Text('Bs ${resumen.total.toStringAsFixed(2)}', style: AppTextStyles.price.copyWith(fontSize: 18)),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _puedeConfirmar ? _confirmar : null,
              child: Text(_confirmando ? 'PROCESANDO...' : 'CONFIRMAR COMPRA'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSucursales() {
    if (_ciudadSeleccionadaId == null) {
      return Text('Selecciona una ciudad para ver sucursales disponibles.', style: AppTextStyles.bodyMuted);
    }
    if (_cargandoSucursales) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: AppSpacing.lg),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      );
    }
    final error = _errorSucursales;
    if (error != null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(error, style: AppTextStyles.bodyMuted),
          TextButton(
            onPressed: () => _cargarSucursales(_ciudadSeleccionadaId!),
            child: const Text('Reintentar'),
          ),
        ],
      );
    }
    if (!_sucursalesConsultadas || _sucursales.isEmpty) {
      return Text('Sin sucursales en esta ciudad.', style: AppTextStyles.bodyMuted);
    }

    final haySucursalDisponible = _sucursales.any((s) => s.disponibleParaCompra);
    if (!haySucursalDisponible) {
      return Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: AppColors.divider),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Sin disponibilidad', style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Text(
              'Ninguna sucursal de esta ciudad tiene disponibilidad para todas las prendas seleccionadas.',
              style: AppTextStyles.bodyMuted,
            ),
          ],
        ),
      );
    }

    return Column(
      children: _sucursales.map((sucursal) {
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: _SucursalCompraCard(
            sucursal: sucursal,
            seleccionada: sucursal.id == _sucursalSeleccionadaId,
            onTap: () => _seleccionarSucursal(sucursal),
          ),
        );
      }).toList(),
    );
  }
}

/// El backend de CU22 SIEMPRE devuelve texto ya profesional en `detail` (ver
/// CU22_RealizarCompraDigital/router.py) -- `ApiClient` antepone un prefijo
/// técnico ("Error HTTP 422: ", "Solicitud inválida: ", etc.) que esta
/// pantalla no debe mostrar. Se muestra solo lo que el backend redactó,
/// nunca el código HTTP ni JSON -- Flutter recibe la respuesta real y
/// SOLAMENTE cambia la presentación, nunca oculta un error real.
String _mensajeAmigable(ApiException e) {
  if (e.statusCode == null) {
    return 'No se pudo conectar. Revisa tu conexión e inténtalo de nuevo.';
  }
  final indice = e.message.indexOf(': ');
  return indice == -1 ? e.message : e.message.substring(indice + 2);
}

/// Bloque de error a pantalla completa con una única acción -- usado cuando
/// no hay nada que mostrar todavía (ej. carrito sin prendas seleccionadas):
/// "Reintentar" no ayudaría ahí, así que la acción es configurable.
class _ErrorConAccion extends StatelessWidget {
  const _ErrorConAccion({required this.mensaje, required this.etiquetaAccion, required this.onAccion});

  final String mensaje;
  final String etiquetaAccion;
  final VoidCallback onAccion;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: const BoxDecoration(color: AppColors.surface, shape: BoxShape.circle),
              child: const Icon(Icons.shopping_bag_outlined, size: 30, color: AppColors.burgundy),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(mensaje, style: AppTextStyles.bodyMuted, textAlign: TextAlign.center),
            const SizedBox(height: AppSpacing.lg),
            ElevatedButton(onPressed: onAccion, child: Text(etiquetaAccion.toUpperCase())),
          ],
        ),
      ),
    );
  }
}

/// Línea de compra de solo lectura -- imagen, nombre, color/talla y precio
/// (con precio anterior tachado + porcentaje si está en promoción). A
/// diferencia de la tarjeta del carrito (CU21), aquí no hay checkbox ni
/// "Eliminar": esta pantalla solo confirma qué se va a comprar, modificar
/// la selección sigue siendo responsabilidad del carrito.
class _LineaCompraCard extends StatelessWidget {
  const _LineaCompraCard({required this.linea});

  final LineaCompraOut linea;

  @override
  Widget build(BuildContext context) {
    final imagenUrl = MediaUrl.resolve(linea.producto.imagenPrincipalUrl);

    return Container(
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(AppRadius.sm),
            child: Container(
              width: 52,
              height: 52,
              color: AppColors.cream,
              child: imagenUrl != null
                  ? Image.network(
                      imagenUrl,
                      fit: BoxFit.cover,
                      errorBuilder: (_, _, _) => const _ImagenPlaceholder(),
                    )
                  : const _ImagenPlaceholder(),
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  linea.producto.nombre,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600),
                ),
                Text(
                  '${linea.variante.color.nombre} · Talla ${linea.variante.talla.nombre}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppTextStyles.bodyMuted,
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (linea.enPromocion)
                Text('Bs ${linea.precioBase.toStringAsFixed(2)}', style: AppTextStyles.priceStrike),
              Text(
                'Bs ${linea.precioUnitario.toStringAsFixed(2)}',
                style: (linea.enPromocion ? AppTextStyles.priceDiscount : AppTextStyles.price).copyWith(fontSize: 14),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ImagenPlaceholder extends StatelessWidget {
  const _ImagenPlaceholder();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Icon(Icons.checkroom_outlined, size: 20, color: AppColors.textSecondary),
    );
  }
}

/// Selector de ciudad -- mismo lenguaje visual que el de disponibilidad por
/// sucursal (ver catalogo/producto_detalle_page.dart), sin autoseleccionar
/// ninguna ciudad.
class _SelectorCiudadCompra extends StatelessWidget {
  const _SelectorCiudadCompra({
    required this.ciudades,
    required this.ciudadSeleccionadaId,
    required this.cargando,
    required this.onChanged,
  });

  final List<Ciudad> ciudades;
  final int? ciudadSeleccionadaId;
  final bool cargando;
  final ValueChanged<int?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.burgundy, width: 1.2),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<int>(
          value: ciudadSeleccionadaId,
          isExpanded: true,
          hint: Text(
            cargando ? 'Cargando ciudades...' : 'Selecciona una ciudad',
            style: AppTextStyles.body.copyWith(color: AppColors.textSecondary),
          ),
          icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.burgundy),
          dropdownColor: AppColors.cream,
          items: ciudades
              .map(
                (ciudad) => DropdownMenuItem<int>(
                  value: ciudad.id,
                  child: Text(ciudad.nombre, style: AppTextStyles.body),
                ),
              )
              .toList(),
          onChanged: (cargando || ciudades.isEmpty) ? null : onChanged,
        ),
      ),
    );
  }
}

/// Tarjeta de sucursal para retiro -- nombre + dirección (dato real de
/// `SucursalCompraOut`, no "Disponible/Agotado" como en CU12: aquí el
/// backend ya evaluó si esa sucursal cubre TODA la compra a la vez). Solo
/// tocable si `disponibleParaCompra`.
class _SucursalCompraCard extends StatelessWidget {
  const _SucursalCompraCard({required this.sucursal, required this.seleccionada, required this.onTap});

  final SucursalCompraOut sucursal;
  final bool seleccionada;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final disponible = sucursal.disponibleParaCompra;
    return GestureDetector(
      onTap: disponible ? onTap : null,
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm + 2),
        decoration: BoxDecoration(
          color: seleccionada ? AppColors.red.withValues(alpha: 0.08) : AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(
            color: seleccionada
                ? AppColors.red
                : (disponible ? AppColors.burgundy.withValues(alpha: 0.35) : AppColors.divider),
            width: seleccionada ? 1.4 : 1,
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              seleccionada ? Icons.check_circle : Icons.storefront_outlined,
              size: 16,
              color: seleccionada ? AppColors.red : AppColors.burgundy,
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    sucursal.nombre,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w500),
                  ),
                  Text(
                    sucursal.direccion,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTextStyles.bodyMuted,
                  ),
                  if (!disponible) ...[
                    const SizedBox(height: 2),
                    Text(
                      'No disponible para todas las prendas',
                      style: AppTextStyles.bodyMuted.copyWith(color: AppColors.textSecondary, fontSize: 11),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
