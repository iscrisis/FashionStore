import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Icon, IconName } from '../../../core/ui/icon/icon';

interface ProveedorNavItem {
  label: string;
  icon: IconName;
  route: string;
  exact?: boolean;
}

@Component({
  selector: 'app-proveedor-sidebar',
  imports: [RouterLink, RouterLinkActive, Icon],
  templateUrl: './proveedor-sidebar.html',
  styleUrl: './proveedor-sidebar.scss',
})
export class ProveedorSidebar {
  protected readonly navItems: ProveedorNavItem[] = [
    { label: 'Inicio', icon: 'dashboard', route: '/proveedor', exact: true },
    { label: 'Mis productos', icon: 'products', route: '/proveedor/mis-productos' },
    { label: 'Enviar producto', icon: 'plus', route: '/proveedor/enviar-producto' },
    { label: 'Disponibilidad', icon: 'power', route: '/proveedor/disponibilidad' },
    { label: 'Mi perfil', icon: 'user', route: '/proveedor/mi-perfil' },
  ];
}
