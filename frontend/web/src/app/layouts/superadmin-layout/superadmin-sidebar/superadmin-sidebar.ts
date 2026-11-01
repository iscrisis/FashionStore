import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Icon, IconName } from '../../../core/ui/icon/icon';

interface SuperadminNavItem {
  label: string;
  icon: IconName;
  route?: string;
}

@Component({
  selector: 'app-superadmin-sidebar',
  imports: [RouterLink, RouterLinkActive, Icon],
  templateUrl: './superadmin-sidebar.html',
  styleUrl: './superadmin-sidebar.scss',
})
export class SuperadminSidebar {
  protected readonly navItems: SuperadminNavItem[] = [
    { label: 'Dashboard', icon: 'dashboard', route: '/superadmin' },
    { label: 'Empresas', icon: 'branches', route: '/superadmin/empresas' },
    { label: 'Planes SaaS', icon: 'products', route: '/superadmin/planes' },
  ];

  protected readonly actions: SuperadminNavItem[] = [
    { label: 'Registrar empresa', icon: 'plus', route: '/registrar-empresa' },
  ];
}
