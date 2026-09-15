import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Icon, IconName } from '../../../core/ui/icon/icon';

interface EncargadoNavItem {
  label: string;
  icon: IconName;
  route: string;
  exact?: boolean;
}

@Component({
  selector: 'app-encargado-sidebar',
  imports: [RouterLink, RouterLinkActive, Icon],
  templateUrl: './encargado-sidebar.html',
  styleUrl: './encargado-sidebar.scss',
})
export class EncargadoSidebar {
  // "Mi perfil" apunta a la ruta propia del Encargado (hija de /encargado),
  // NUNCA a '/mi-perfil' -- esa es la pública de Cliente, en otro layout.
  // "Inventario" es CU14 (CU14_ConsultarInventario, restaurado del stash) --
  // consulta y ajusta el stock real de SU sucursal, resuelta siempre desde
  // el usuario autenticado, nunca desde la URL.
  // "Recepción de mercadería" es CU15: registra mercadería recibida de un
  // proveedor y suma a ese mismo stock -- misma sucursal, misma seguridad.
  // "Movimientos de inventario" es CU16: ajustes manuales justificados
  // (positivos/negativos) sobre ese mismo stock, con trazabilidad -- distinto
  // de CU15 (recepción de proveedor).
  protected readonly navItems: EncargadoNavItem[] = [
    { label: 'Inicio', icon: 'dashboard', route: '/encargado', exact: true },
    { label: 'Inventario', icon: 'inventory', route: '/encargado/inventario' },
    { label: 'Recepción de mercadería', icon: 'suppliers', route: '/encargado/recepcion-mercaderia' },
    { label: 'Movimientos de inventario', icon: 'edit', route: '/encargado/movimientos-inventario' },
    { label: 'Mi perfil', icon: 'user', route: '/encargado/mi-perfil' },
  ];
}
