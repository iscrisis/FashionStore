import 'package:flutter/material.dart';

import '../asistente_ia/widgets/asistente_ia_overlay.dart';
import '../auth/auth_service.dart';
import '../auth/models/usuario_sesion.dart';
import '../carrito/mi_carrito_page.dart';
import '../catalogo/catalogo_page.dart';
import '../home/home_page.dart';
import '../perfil/perfil_page.dart';
import '../reservas/mis_reservas_page.dart';

/// Shell de navegación inferior. Los 5 módulos corresponden a CU reales del
/// Cliente (CU11 catálogo, CU17/18 reservas, CU21 carrito, CU01/CU04
/// perfil) -- no se agrega "Favoritos" porque no existe ese CU en el
/// backend.
///
/// "Inicio", "Explorar" son públicos y ya estaban completos. "Perfil",
/// "Reservas" y "Carrito" ya integran CU01 (Iniciar sesión) real.
///
/// La sesión (si existe) se restaura una sola vez al abrir la app -- sin
/// llamar a ningún endpoint, ver AuthService.sesionGuardada() -- y se
/// mantiene aquí, en el nivel más alto de la navegación, porque más de un
/// tab (Reservas/Carrito) necesita saber si hay Cliente autenticado.
class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  final _authService = AuthService();

  static const int _indiceReservas = 2;
  static const int _indiceCarrito = 3;

  int _index = 0;
  UsuarioSesion? _usuario;

  // CU18/CU21 (Consultar reservas / Usar carrito): MisReservasPage y
  // MiCarritoPage reciben una key distinta cada vez que el Cliente vuelve a
  // tocar su tab (ver build()) -- eso fuerza reconstruir el widget desde
  // cero, así siempre revalida la sesión y vuelve a consultar el backend en
  // vez de quedarse con un estado (sin sesión, o datos ya desactualizados)
  // de la última vez que se montó, mientras seguía vivo de fondo dentro del
  // IndexedStack.
  int _reservasVisitTick = 0;
  int _carritoVisitTick = 0;

  @override
  void initState() {
    super.initState();
    _restaurarSesion();
  }

  Future<void> _restaurarSesion() async {
    final usuario = await _authService.sesionGuardada();
    if (!mounted || usuario == null) return;
    setState(() => _usuario = usuario);
  }

  void _irA(int index) {
    setState(() {
      _index = index;
      if (index == _indiceReservas) _reservasVisitTick++;
      if (index == _indiceCarrito) _carritoVisitTick++;
    });
  }

  void _onSesionIniciada(UsuarioSesion usuario) {
    setState(() => _usuario = usuario);
  }

  Future<void> _cerrarSesion() async {
    await _authService.cerrarSesion();
    if (!mounted) return;
    setState(() => _usuario = null);
  }

  @override
  Widget build(BuildContext context) {
    final paginas = [
      HomePage(onAbrirCarrito: () => _irA(3), onAbrirPerfil: () => _irA(4)),
      const CatalogoPage(titulo: 'Explorar'),
      MisReservasPage(key: ValueKey(_reservasVisitTick)),
      MiCarritoPage(key: ValueKey(_carritoVisitTick), onExplorar: () => _irA(1)),
      PerfilPage(
        usuario: _usuario,
        onSesionIniciada: _onSesionIniciada,
        onCerrarSesion: _cerrarSesion,
      ),
    ];

    return Scaffold(
      // El asistente IA (CU29) vive por encima del IndexedStack, no dentro
      // de una de sus páginas -- mismo criterio que Angular (montado en
      // public-layout, fuera del <router-outlet>): la conversación sobrevive
      // aunque el Cliente cambie de tab (Inicio/Explorar/Reservas/Carrito/
      // Perfil), y nunca tapa el bottomNavigationBar (fuera de este Stack).
      body: Stack(
        children: [
          IndexedStack(index: _index, children: paginas),
          const AsistenteIaOverlay(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _index,
        onTap: _irA,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_outlined), activeIcon: Icon(Icons.home), label: 'Inicio'),
          BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Explorar'),
          BottomNavigationBarItem(
            icon: Icon(Icons.event_available_outlined),
            activeIcon: Icon(Icons.event_available),
            label: 'Reservas',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.shopping_bag_outlined),
            activeIcon: Icon(Icons.shopping_bag),
            label: 'Carrito',
          ),
          BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Perfil'),
        ],
      ),
    );
  }
}
