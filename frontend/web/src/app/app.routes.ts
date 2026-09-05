import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./layouts/public-layout/public-layout').then((m) => m.PublicLayout),
    children: [
      {
        path: '',
        loadComponent: () => import('./features/public/home/home').then((m) => m.Home),
        title: 'Fashion Store',
      },
      {
        path: 'login',
        loadComponent: () =>
          import('./usuarios-y-accesos/cu01-iniciar-sesion/login').then((m) => m.Login),
        title: 'Iniciar sesión · Fashion Store',
      },
    ],
  },
  {
    path: 'admin',
    loadComponent: () =>
      import('./layouts/admin-layout/admin-layout').then((m) => m.AdminLayout),
    canActivate: [authGuard, roleGuard('ADMINISTRADOR')],
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadComponent: () =>
          import('./features/admin/dashboard/dashboard').then((m) => m.Dashboard),
        title: 'Panel de administración · Fashion Store Admin',
        data: {
          headerTitle: 'Panel de administración',
          headerSubtitle: 'Resumen general de FashionStore.',
        },
      },
      {
        path: 'catalogo/atributos',
        loadComponent: () =>
          import('./sucursales-catalogo/atributos/catalog-attributes').then(
            (m) => m.CatalogAttributes,
          ),
        title: 'Categorías, tallas y colores · Fashion Store Admin',
        data: {
          headerTitle: 'Gestión del catálogo',
          headerSubtitle: 'Administra los datos base utilizados para registrar las prendas.',
        },
      },
      {
        path: 'usuarios-roles',
        loadComponent: () =>
          import('./usuarios-y-accesos/cu05-gestionar-usuarios-roles/usuarios-roles').then(
            (m) => m.UsuariosRoles,
          ),
        title: 'Usuarios y roles · Fashion Store Admin',
        data: {
          headerTitle: 'Usuarios y roles',
          headerSubtitle: 'Administra las cuentas internas de FashionStore y sus roles de acceso.',
        },
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
