import { Component, output } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Icon, IconName } from '../../../core/ui/icon/icon';

interface CajeroNavItem {
  label: string;
  icon: IconName;
  route: string;
  exact?: boolean;
}

@Component({
  selector: 'app-cajero-sidebar',
  imports: [RouterLink, RouterLinkActive, Icon],
  templateUrl: './cajero-sidebar.html',
  styleUrl: './cajero-sidebar.scss',
})
export class CajeroSidebar {
  // "Ventas" es CU24 (venta directa). "Reservas para caja" es la
  // integración de CU20 ya existente (reservas-pendientes.ts) -- prendas
  // que el Encargado dejó LISTA_PARA_CAJA. "Historial" es CU27 -- ítem
  // propio, separado de "Ventas" a propósito (requerimiento explícito: no
  // mezclarlos). "Devoluciones y cambios" es CU26. "Mi perfil" reutiliza el
  // mismo componente MiPerfil (CU04) que ya usan Cliente/Encargado/
  // Proveedor, nunca duplicado.
  protected readonly navItems: CajeroNavItem[] = [
    { label: 'Inicio', icon: 'dashboard', route: '/cajero', exact: true },
    { label: 'Ventas', icon: 'sales', route: '/cajero/ventas/nueva' },
    { label: 'Reservas para caja', icon: 'reservations', route: '/cajero/reservas-pendientes' },
    { label: 'Historial', icon: 'reports', route: '/cajero/historial' },
    { label: 'Devoluciones y cambios', icon: 'edit', route: '/cajero/devoluciones' },
    { label: 'Mi perfil', icon: 'user', route: '/cajero/mi-perfil' },
  ];

  // Emitido al elegir cualquier ítem -- CajeroLayout lo usa para cerrar el
  // drawer en tablet/móvil (en escritorio no tiene efecto, el sidebar ya
  // está siempre visible).
  readonly navegar = output<void>();
}
