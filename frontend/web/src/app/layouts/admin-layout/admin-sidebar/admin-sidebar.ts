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
    { label: 'Sucursales', icon: 'branches', route: '/admin/sucursales' },
    { label: 'Categorías, tallas y colores', icon: 'catalog', route: '/admin/catalogo/atributos' },
    { label: 'Temporadas y colecciones', icon: 'seasons', route: '/admin/catalogo/temporadas' },
    { label: 'Proveedores', icon: 'suppliers', route: '/admin/proveedores' },
    { label: 'Productos', icon: 'products', route: '/admin/catalogo/productos' },
    { label: 'Usuarios y roles', icon: 'users', route: '/admin/usuarios-roles' },
  ];
}
