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
      {
        path: 'recuperar-contrasena',
        loadComponent: () =>
          import('./usuarios-y-accesos/cu03-recuperar-contrasena/solicitar-recuperacion').then(
            (m) => m.SolicitarRecuperacion,
          ),
        title: 'Recuperar contraseña · Fashion Store',
      },
      {
        path: 'restablecer-contrasena',
        loadComponent: () =>
          import('./usuarios-y-accesos/cu03-recuperar-contrasena/restablecer-contrasena').then(
            (m) => m.RestablecerContrasena,
          ),
        title: 'Restablecer contraseña · Fashion Store',
      },
      {
        path: 'catalogo',
        loadComponent: () =>
          import('./features/public/catalogo/catalogo-page/catalogo-page').then(
            (m) => m.CatalogoPage,
          ),
        title: 'Catálogo · Fashion Store',
      },
      {
        path: 'producto/:id',
        loadComponent: () =>
          import('./features/public/catalogo/producto-detalle/producto-detalle').then(
            (m) => m.ProductoDetalle,
          ),
        title: 'Detalle de producto · Fashion Store',
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
        path: 'catalogo/temporadas',
        loadComponent: () =>
          import('./sucursales-catalogo/cu10-gestionar-temporadas-colecciones/temporadas-colecciones').then(
            (m) => m.TemporadasColecciones,
          ),
        title: 'Temporadas y colecciones · Fashion Store Admin',
        data: {
          headerTitle: 'Temporadas y colecciones',
          headerSubtitle: 'Configura las temporadas de FashionStore y las colecciones que agrupan.',
        },
      },
      {
        path: 'proveedores',
        loadComponent: () =>
          import('./sucursales-catalogo/gestion-proveedores/gestion-proveedores').then(
            (m) => m.GestionProveedores,
          ),
        title: 'Proveedores · Fashion Store Admin',
        data: {
          headerTitle: 'Proveedores',
          headerSubtitle: 'Administra los proveedores externos de FashionStore.',
        },
      },
      {
        path: 'catalogo/productos',
        loadComponent: () =>
          import('./sucursales-catalogo/cu08-gestionar-productos/gestionar-productos').then(
            (m) => m.GestionarProductos,
          ),
        title: 'Productos · Fashion Store Admin',
        data: {
          headerTitle: 'Productos',
          headerSubtitle: 'Gestiona el catálogo de prendas de FashionStore.',
        },
      },
      {
        path: 'sucursales',
        loadComponent: () =>
          import('./sucursales-catalogo/cu06-gestionar-sucursales/sucursales').then(
            (m) => m.Sucursales,
          ),
        title: 'Gestionar sucursales · Fashion Store Admin',
        data: {
          headerTitle: 'Gestionar sucursales',
          headerSubtitle: 'Administra las sucursales físicas de FashionStore.',
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
  {
    path: 'proveedor',
    loadComponent: () =>
      import('./layouts/proveedor-layout/proveedor-layout').then((m) => m.ProveedorLayout),
    canActivate: [authGuard, roleGuard('PROVEEDOR')],
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadComponent: () => import('./features/proveedor/inicio/inicio').then((m) => m.Inicio),
        title: 'Panel de Proveedor · Fashion Store',
        data: {
          headerTitle: 'Panel de Proveedor',
          headerSubtitle: 'Resumen de tu actividad en FashionStore.',
        },
      },
      {
        path: 'mis-productos',
        loadComponent: () =>
          import('./features/proveedor/mis-productos/mis-productos').then((m) => m.MisProductos),
        title: 'Mis productos · Fashion Store Proveedor',
        data: {
          headerTitle: 'Mis productos',
          headerSubtitle: 'Consulta y edita la información de tus prendas enviadas.',
        },
      },
      {
        path: 'enviar-producto',
        loadComponent: () =>
          import('./features/proveedor/enviar-producto/enviar-producto').then(
            (m) => m.EnviarProducto,
          ),
        title: 'Enviar producto · Fashion Store Proveedor',
        data: {
          headerTitle: 'Enviar producto',
          headerSubtitle: 'Comparte una nueva prenda que ofreces a FashionStore.',
        },
      },
      {
        path: 'disponibilidad',
        loadComponent: () =>
          import('./features/proveedor/disponibilidad/disponibilidad').then(
            (m) => m.Disponibilidad,
          ),
        title: 'Disponibilidad · Fashion Store Proveedor',
        data: {
          headerTitle: 'Disponibilidad',
          headerSubtitle: 'Informa qué prendas tienes disponibles actualmente.',
        },
      },
      {
        path: 'mi-perfil',
        loadComponent: () =>
          import('./features/proveedor/mi-perfil/mi-perfil').then((m) => m.MiPerfil),
        title: 'Mi perfil · Fashion Store Proveedor',
        data: {
          headerTitle: 'Mi perfil',
          headerSubtitle: 'Datos de contacto de tu empresa.',
        },
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
