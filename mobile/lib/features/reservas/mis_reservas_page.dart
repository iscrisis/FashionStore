import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/storage/token_storage.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/media_url.dart';
import '../../shared/widgets/async_state_message.dart';
import '../auth/auth_service.dart';
import '../auth/login_page.dart';
import '../auth/models/usuario_sesion.dart';
import 'cancelar_reserva_service.dart';
import 'consultar_reservas_service.dart';
import 'models/reserva.dart';
import 'reserva_formato.dart';
import 'widgets/cancelar_reserva_dialog.dart';

enum _Estado { verificandoSesion, sinSesion, cargando, listo, error }

/// CU18 -- pestañas de "Mis reservas", calcadas de `TABS` en Angular
/// (frontend/web/.../mis-reservas.ts): una reserva vive en una sola pestaña
/// a la vez, agrupada por `estado_general` (agregado de TODOS sus detalles,
/// ver Models/reserva.py:calcular_estado_general en el backend) -- nunca por
/// el estado de un detalle individual. Filtro 100% en memoria sobre la MISMA
/// respuesta de `GET /reservas/mias`: cambiar de pestaña nunca dispara una
/// llamada nueva al backend.
enum _TabReserva {
  pendientes,
  atendidas,
  canceladas;

  String get etiqueta {
    switch (this) {
      case _TabReserva.pendientes:
        return 'Pendientes';
      case _TabReserva.atendidas:
        return 'Atendidas';
      case _TabReserva.canceladas:
        return 'Canceladas';
    }
  }

  Set<EstadoReserva> get estados {
    switch (this) {
      case _TabReserva.pendientes:
        return const {
          EstadoReserva.pendiente,
          EstadoReserva.preparada,
          EstadoReserva.enAtencion,
          EstadoReserva.listaParaCaja,
        };
      case _TabReserva.atendidas:
        return const {EstadoReserva.atendida};
      case _TabReserva.canceladas:
        return const {EstadoReserva.cancelada, EstadoReserva.vencida};
    }
  }
}

/// CU18 -- Consultar reserva (Cliente). Tab "Reservas" del bottom nav.
///
/// Sin sesión: se comporta igual que el tab Perfil (ver perfil_page.dart) --
/// ES directamente CU01 (Iniciar sesión), sin pantalla intermedia. Con
/// sesión, consulta SIEMPRE el backend real (`GET /reservas/mias`, el mismo
/// endpoint de CU17) -- nunca hay una reserva "de mentira" guardada
/// localmente; FastAPI es la única fuente de verdad.
///
/// AppShell le asigna una `key` que cambia cada vez que el Cliente vuelve a
/// tocar este tab (ver app_shell.dart, `_reservasVisitTick`) -- eso fuerza
/// que este widget se reconstruya desde cero y vuelva a verificar la sesión
/// en cada visita, en vez de quedarse con un estado "sin sesión" obsoleto si
/// el Cliente inició sesión desde otro lugar (ej. el botón "Reservar" del
/// detalle de producto) mientras este tab seguía montado en el IndexedStack.
class MisReservasPage extends StatefulWidget {
  const MisReservasPage({super.key});

  @override
  State<MisReservasPage> createState() => _MisReservasPageState();
}

class _MisReservasPageState extends State<MisReservasPage> {
  final _authService = AuthService();
  final _service = ConsultarReservasService();
  final _cancelarService = CancelarReservaService();

  _Estado _estado = _Estado.verificandoSesion;
  List<ReservaOut> _reservas = [];
  _TabReserva _tabActiva = _TabReserva.pendientes;

  List<ReservaOut> get _reservasFiltradas {
    return _reservas.where((r) => _tabActiva.estados.contains(r.estadoGeneral)).toList();
  }

  void _seleccionarTab(_TabReserva tab) {
    setState(() => _tabActiva = tab);
  }

  @override
  void initState() {
    super.initState();
    _verificarSesion();
  }

  Future<void> _verificarSesion() async {
    final usuario = await _authService.sesionGuardada();
    if (!mounted) return;
    if (usuario == null) {
      setState(() => _estado = _Estado.sinSesion);
      return;
    }
    _cargarReservas();
  }

  Future<void> _cargarReservas() async {
    setState(() => _estado = _Estado.cargando);
    final token = await TokenStorage.getToken();
    if (token == null) {
      if (!mounted) return;
      setState(() => _estado = _Estado.sinSesion);
      return;
    }
    try {
      final reservas = await _service.listarMias(token: token);
      if (!mounted) return;
      setState(() {
        _reservas = reservas;
        _estado = _Estado.listo;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.statusCode == 401) {
        // Mismo criterio que AuthService.obtenerMiPerfil(): un 401 significa
        // que el token ya no es válido para FastAPI -- se limpia la sesión y
        // se trata exactamente como "sin sesión", nunca como un error de red.
        await TokenStorage.clearSession();
        setState(() => _estado = _Estado.sinSesion);
        return;
      }
      setState(() => _estado = _Estado.error);
    } catch (_) {
      if (!mounted) return;
      setState(() => _estado = _Estado.error);
    }
  }

  void _onLoginExitoso(UsuarioSesion usuario) {
    _cargarReservas();
  }

  /// CU19 -- Cancelar reserva: abre el modal de confirmación y, si el
  /// Cliente confirma, cancela ESE detalle (prenda) sin afectar al resto de
  /// la reserva. Mismo criterio que `onDetalleCancelado` en Angular
  /// (mis-reservas.ts): reemplaza el detalle localmente para feedback
  /// instantáneo, y además refresca la lista completa en silencio (sin
  /// mostrar el loader) para que `estado_general` -- un agregado que SOLO el
  /// backend recalcula (ver Models/reserva.py) -- quede al día si ese cambio
  /// afectó a toda la cabecera.
  Future<void> _cancelarDetalle(ReservaOut reserva, ReservaDetalleOut detalle) async {
    final token = await TokenStorage.getToken();
    if (token == null) {
      if (!mounted) return;
      setState(() => _estado = _Estado.sinSesion);
      return;
    }
    if (!mounted) return;

    final actualizado = await mostrarCancelarReservaDialog(
      context,
      reserva: reserva,
      detalle: detalle,
      onConfirmar: () => _cancelarService.cancelarDetalle(detalleId: detalle.id, token: token),
    );
    if (actualizado == null || !mounted) return;

    setState(() {
      _reservas = _reservas.map((r) {
        if (r.id != reserva.id) return r;
        return ReservaOut(
          id: r.id,
          codigoReserva: r.codigoReserva,
          sucursal: r.sucursal,
          estadoGeneral: r.estadoGeneral,
          fechaReserva: r.fechaReserva,
          horaInicio: r.horaInicio,
          horaFin: r.horaFin,
          fechaCreacion: r.fechaCreacion,
          detalles: r.detalles.map((d) => d.id == actualizado.id ? actualizado : d).toList(),
        );
      }).toList();
    });
    _mostrarMensaje('Prenda cancelada correctamente.');

    // Refresco silencioso (sin loader) -- un fallo aquí no es crítico, el
    // parche local ya quedó aplicado.
    try {
      final token2 = await TokenStorage.getToken();
      if (token2 == null || !mounted) return;
      final reservas = await _service.listarMias(token: token2);
      if (!mounted) return;
      setState(() => _reservas = reservas);
    } catch (_) {
      // Silencioso a propósito -- ver comentario arriba.
    }
  }

  void _mostrarMensaje(String texto) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(texto), backgroundColor: AppColors.burgundy),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_estado == _Estado.sinSesion) {
      return LoginPage(onLoginExitoso: _onLoginExitoso);
    }

    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(title: const Text('Reservas')),
      body: SafeArea(
        child: Column(
          children: [
            if (_estado != _Estado.verificandoSesion)
              _TabsReserva(activa: _tabActiva, onSeleccionar: _seleccionarTab),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    switch (_estado) {
      case _Estado.sinSesion:
        // Ya se resolvió arriba, en build() -- nunca llega aquí.
        return const SizedBox.shrink();
      case _Estado.verificandoSesion:
      case _Estado.cargando:
        return const Center(child: CircularProgressIndicator(strokeWidth: 2));
      case _Estado.error:
        return Center(
          child: AsyncStateMessage(
            message: 'No se pudieron cargar tus reservas.',
            icon: Icons.error_outline,
            onRetry: _cargarReservas,
          ),
        );
      case _Estado.listo:
        final reservas = _reservasFiltradas;
        if (reservas.isEmpty) {
          return _EstadoVacioCategoria(onRefrescar: _cargarReservas);
        }
        return RefreshIndicator(
          color: AppColors.red,
          onRefresh: _cargarReservas,
          child: ListView.separated(
            padding: const EdgeInsets.all(AppSpacing.lg),
            itemCount: reservas.length,
            separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.md),
            itemBuilder: (context, index) {
              final reserva = reservas[index];
              return _ReservaCard(
                reserva: reserva,
                onCancelarDetalle: (detalle) => _cancelarDetalle(reserva, detalle),
              );
            },
          ),
        );
    }
  }
}

/// Barra de pestañas de CU18 -- fila de "chips" tipo píldora sobre un fondo
/// `AppColors.surface`, nunca el `TabBar` genérico de Material (subrayado +
/// ripple estándar): mismo lenguaje visual que el resto de selectores de la
/// app (ver `_HoraChip`/`_DiaChip` en crear_reserva_sheet.dart).
class _TabsReserva extends StatelessWidget {
  const _TabsReserva({required this.activa, required this.onSeleccionar});

  final _TabReserva activa;
  final ValueChanged<_TabReserva> onSeleccionar;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.md, AppSpacing.lg, 0),
      child: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: Row(
          children: [
            for (final tab in _TabReserva.values)
              Expanded(
                child: _TabChip(
                  etiqueta: tab.etiqueta,
                  seleccionado: tab == activa,
                  onTap: () => onSeleccionar(tab),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _TabChip extends StatelessWidget {
  const _TabChip({required this.etiqueta, required this.seleccionado, required this.onTap});

  final String etiqueta;
  final bool seleccionado;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(vertical: 10),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: seleccionado ? AppColors.red : Colors.transparent,
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: Text(
          etiqueta,
          style: AppTextStyles.bodyMuted.copyWith(
            color: seleccionado ? AppColors.cream : AppColors.textSecondary,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

/// "Sin reservas en esta pestaña" -- mismo lenguaje visual que el resto de
/// estados vacíos de la app (ícono en círculo + título + mensaje, ver
/// MisComprasPage/PerfilPage), sin inventar ningún dato ni contador. El
/// mensaje es el mismo sin importar la pestaña activa (Pendientes/Atendidas/
/// Canceladas) -- a diferencia de Angular, que varía el texto por pestaña,
/// aquí se mantiene un único mensaje genérico. `onRefrescar` permite
/// deslizar para reintentar aunque esta pestaña esté vacía (útil si el
/// Cliente acaba de reservar o cancelar desde otro lugar).
class _EstadoVacioCategoria extends StatelessWidget {
  const _EstadoVacioCategoria({required this.onRefrescar});

  final Future<void> Function() onRefrescar;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      color: AppColors.red,
      onRefresh: onRefrescar,
      child: LayoutBuilder(
        builder: (context, constraints) {
          return SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: ConstrainedBox(
              constraints: BoxConstraints(minHeight: constraints.maxHeight),
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 72,
                        height: 72,
                        decoration: const BoxDecoration(color: AppColors.surface, shape: BoxShape.circle),
                        child: const Icon(
                          Icons.event_available_outlined,
                          size: 30,
                          color: AppColors.burgundy,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      Text('Sin reservas', style: AppTextStyles.sectionTitle, textAlign: TextAlign.center),
                      const SizedBox(height: AppSpacing.sm),
                      Text(
                        'No tienes reservas en esta categoría',
                        style: AppTextStyles.bodyMuted,
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

/// Tarjeta de una reserva -- cabecera (código + estado), cada prenda
/// (`detalles`, normalmente una sola: CU17 todavía no expone un carrito) y
/// el resumen de sucursal + fecha/horario. Estética de app de moda: tarjeta
/// limpia, sin tabla ni aspecto administrativo.
class _ReservaCard extends StatelessWidget {
  const _ReservaCard({required this.reserva, required this.onCancelarDetalle});

  final ReservaOut reserva;
  final ValueChanged<ReservaDetalleOut> onCancelarDetalle;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Reserva ${reserva.codigoReserva}',
                  style: AppTextStyles.bodyMuted.copyWith(color: AppColors.burgundy, fontWeight: FontWeight.w600),
                ),
              ),
              _EstadoBadge(estado: reserva.estadoGeneral),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          for (final detalle in reserva.detalles) ...[
            _DetallePrenda(detalle: detalle, onCancelar: () => onCancelarDetalle(detalle)),
            if (detalle != reserva.detalles.last) const SizedBox(height: AppSpacing.sm),
          ],
          const Padding(
            padding: EdgeInsets.symmetric(vertical: AppSpacing.sm),
            child: Divider(height: 1),
          ),
          _FilaInfo(
            icono: Icons.storefront_outlined,
            texto: '${reserva.sucursal.nombre} · ${reserva.sucursal.ciudad.nombre}',
          ),
          const SizedBox(height: AppSpacing.xs),
          _FilaInfo(
            icono: Icons.event_outlined,
            texto:
                '${formatearFechaReserva(reserva.fechaReserva)} · '
                '${formatearHorarioReserva(reserva.horaInicio, reserva.horaFin)}',
          ),
        ],
      ),
    );
  }
}

/// CU19 -- una prenda solo se puede cancelar mientras el Cliente todavía no
/// llegó a la sucursal por ella (PENDIENTE o PREPARADA, mismo criterio que
/// `_ESTADOS_CANCELABLES` en el backend, CU19_CancelarReserva/service.py, y
/// que `puedeCancelar` en Angular, cancelar-reserva.ts) -- desde EN_ATENCION
/// en adelante (o ya ATENDIDA/CANCELADA/VENCIDA) el botón simplemente no se
/// muestra, nunca deshabilitado.
bool _detallePuedeCancelarse(EstadoReserva estado) {
  return estado == EstadoReserva.pendiente || estado == EstadoReserva.preparada;
}

class _DetallePrenda extends StatelessWidget {
  const _DetallePrenda({required this.detalle, required this.onCancelar});

  final ReservaDetalleOut detalle;
  final VoidCallback onCancelar;

  @override
  Widget build(BuildContext context) {
    final imagenUrl = MediaUrl.resolve(detalle.producto.imagenPrincipalUrl);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.sm),
          child: Container(
            width: 48,
            height: 48,
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
                detalle.producto.nombre,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: AppTextStyles.body.copyWith(fontWeight: FontWeight.w600),
              ),
              Text(
                detalle.cantidad > 1
                    ? '${detalle.variante.color.nombre} · Talla ${detalle.variante.talla.nombre} · x${detalle.cantidad}'
                    : '${detalle.variante.color.nombre} · Talla ${detalle.variante.talla.nombre}',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: AppTextStyles.bodyMuted,
              ),
            ],
          ),
        ),
        if (_detallePuedeCancelarse(detalle.estado))
          TextButton(
            onPressed: onCancelar,
            style: TextButton.styleFrom(
              foregroundColor: AppColors.red,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: const Text('Cancelar', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
          ),
      ],
    );
  }
}

class _ImagenPlaceholder extends StatelessWidget {
  const _ImagenPlaceholder();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Icon(Icons.checkroom_outlined, size: 18, color: AppColors.textSecondary),
    );
  }
}

class _FilaInfo extends StatelessWidget {
  const _FilaInfo({required this.icono, required this.texto});

  final IconData icono;
  final String texto;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icono, size: 14, color: AppColors.burgundy),
        const SizedBox(width: AppSpacing.xs),
        Expanded(
          child: Text(
            texto,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: AppTextStyles.bodyMuted,
          ),
        ),
      ],
    );
  }
}

/// Badge de `estado_general` -- SOLO los 7 valores reales del backend (ver
/// models/reserva.dart: EstadoReserva), coloreados con la paleta existente
/// (rojo/burdeos/dorado/carbón), nunca colores nuevos ni inventados:
///   - PENDIENTE: dorado (a la espera, acento pequeño de marca).
///   - PREPARADA / ATENDIDA: burdeos (avance/cierre normal).
///   - EN_ATENCION / LISTA_PARA_CAJA: rojo FashionStore (el Cliente ya está
///     en la sucursal, el estado más "activo").
///   - CANCELADA / VENCIDA: gris neutro (desenlaces que no llegaron a una
///     atención real).
class _EstadoBadge extends StatelessWidget {
  const _EstadoBadge({required this.estado});

  final EstadoReserva estado;

  @override
  Widget build(BuildContext context) {
    final (Color fondo, Color texto) = switch (estado) {
      EstadoReserva.pendiente => (AppColors.gold, AppColors.charcoal),
      EstadoReserva.preparada || EstadoReserva.atendida => (AppColors.burgundy, AppColors.cream),
      EstadoReserva.enAtencion || EstadoReserva.listaParaCaja => (AppColors.red, AppColors.cream),
      EstadoReserva.cancelada || EstadoReserva.vencida => (AppColors.divider, AppColors.textSecondary),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: fondo, borderRadius: BorderRadius.circular(AppRadius.pill)),
      child: Text(
        estado.etiqueta,
        style: AppTextStyles.bodyMuted.copyWith(color: texto, fontWeight: FontWeight.w600, fontSize: 11),
      ),
    );
  }
}
