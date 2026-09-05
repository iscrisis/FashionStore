import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Icon, IconName } from '../../../core/ui/icon/icon';

interface AdminNavChild {
  label: string;
  route?: string;
}

interface AdminNavItem {
  label: string;
  icon: IconName;
  route?: string;
  children?: AdminNavChild[];
}

@Component({
  selector: 'app-admin-sidebar',
  imports: [RouterLink, RouterLinkActive, Icon],
  templateUrl: './admin-sidebar.html',
  styleUrl: './admin-sidebar.scss',
})
export class AdminSidebar {
  protected readonly navItems: AdminNavItem[] = [
    { label: 'Dashboard', icon: 'dashboard', route: '/admin' },
    { label: 'Sucursales', icon: 'branches' },
    {
      label: 'Catálogo',
      icon: 'catalog',
      children: [
        { label: 'Categorías, tallas y colores', route: '/admin/catalogo/atributos' },
        { label: 'Temporadas y colecciones' },
        { label: 'Productos' },
      ],
    },
    { label: 'Inventario', icon: 'inventory' },
    { label: 'Proveedores', icon: 'suppliers' },
    { label: 'Reservas', icon: 'reservations' },
    { label: 'Ventas', icon: 'sales' },
    {
      label: 'Usuarios y acceso',
      icon: 'users',
      children: [{ label: 'Usuarios y roles', route: '/admin/usuarios-roles' }],
    },
    { label: 'Reportes', icon: 'reports' },
  ];
}
