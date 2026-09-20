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
        // CU02 -- Registrar cliente. Público, sin guard -- el link "¿No
        // tienes cuenta? Regístrate" de login.html ya apuntaba aquí.
        path: 'registro',
        loadComponent: () =>
          import('./usuarios-y-accesos/cu02-registrar-cliente/registrar-cliente').then(
            (m) => m.RegistrarCliente,
          ),
        title: 'Crear cuenta · Fashion Store',
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
        path: 'mi-perfil',
        loadComponent: () =>
          import('./usuarios-y-accesos/cu04-actualizar-perfil/mi-perfil').then((m) => m.MiPerfil),
        canActivate: [authGuard],
        title: 'Mi perfil · Fashion Store',
      },
      {
        // CU18 -- Consultar reserva (Cliente). Sigue dentro del layout
        // público (mismo navbar), igual que 'mi-perfil' -- no es un
        // dashboard nuevo. roleGuard('CLIENTE') además de authGuard porque,
        // a diferencia de 'mi-perfil' (compartido con Encargado/Proveedor),
        // esta pantalla es exclusiva del Cliente.
        path: 'mis-reservas',
        loadComponent: () =>
          import('./features/reservas/mis-reservas/mis-reservas').then((m) => m.MisReservas),
        canActivate: [authGuard, roleGuard('CLIENTE')],
        title: 'Mis reservas · Fashion Store',
      },
      {
        // CU21 -- Usar carrito de compras (Cliente). Sigue dentro del
        // layout público (mismo navbar), igual que 'mis-reservas' -- no es
        // un dashboard nuevo.
        path: 'carrito',
        loadComponent: () =>
          import('./features/carrito/mi-carrito/mi-carrito').then((m) => m.MiCarrito),
        canActivate: [authGuard, roleGuard('CLIENTE')],
        title: 'Mi carrito · Fashion Store',
      },
      {
        // CU22 -- Realizar compra digital (Cliente). A la que lleva
        // "CONTINUAR COMPRA" desde /carrito -- mismo layout público, sigue
        // sin ser un dashboard nuevo.
        path: 'finalizar-compra',
        loadComponent: () =>
          import('./features/compra-digital/finalizar-compra/finalizar-compra').then(
            (m) => m.FinalizarCompra,
          ),
        canActivate: [authGuard, roleGuard('CLIENTE')],
        title: 'Finalizar compra · Fashion Store',
      },
      {
        // CU23 -- Procesar pago electrónico (Cliente). Punto de entrada
        // hacia Stripe Checkout Hosted, al que navega CU22 apenas confirma
        // la Venta -- mismo layout público.
        path: 'pago/iniciar',
        loadComponent: () =>
          import('./features/pago-electronico/iniciar-pago/iniciar-pago').then((m) => m.IniciarPago),
        canActivate: [authGuard, roleGuard('CLIENTE')],
        title: 'Pago · Fashion Store',
      },
      {
        // CU23 -- adonde Stripe redirige de vuelta (success_url/cancel_url,
        // ver CU23_ProcesarPagoElectronico/router.py) tanto si el pago se
        // completó como si el Cliente lo canceló.
        path: 'pago/resultado',
        loadComponent: () =>
          import('./features/pago-electronico/resultado-pago/resultado-pago').then((m) => m.ResultadoPago),
        canActivate: [authGuard, roleGuard('CLIENTE')],
        title: 'Pago · Fashion Store',
      },
      {
        // CU27 -- Consultar historial de compras (Cliente, "Mis compras").
        // Independiente de '/mis-reservas' (CU18, Reserva/RS-XXXXX) -- CU27
        // es Venta/VT-XXXXX, ver features/cliente/historial-compras. Mismo
        // layout público, sigue sin ser un dashboard nuevo.
        path: 'mis-compras',
        loadComponent: () =>
          import('./features/cliente/historial-compras/historial-compras').then(
            (m) => m.HistorialComprasCliente,
          ),
        canActivate: [authGuard, roleGuard('CLIENTE')],
        title: 'Mis compras · Fashion Store',
      },
      {
        // CU31 -- Emitir comprobante de venta (Cliente). A la que navega
        // "Ver comprobante" desde resultado-pago.ts (CU23) apenas se
        // confirma el pago -- mismo layout público, sigue sin ser un
        // dashboard nuevo.
        path: 'comprobante/:ventaId',
        loadComponent: () =>
          import('./features/cliente/comprobantes/comprobante-cliente').then(
            (m) => m.ComprobanteCliente,
          ),
        canActivate: [authGuard, roleGuard('CLIENTE')],
        title: 'Comprobante de compra · Fashion Store',
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
        // El navbar (public-header.ts) ya enlazaba a '/colecciones' -- esta
        // ruta simplemente no existía. Reutiliza CatalogoService.listColecciones()
        // (mismo endpoint público de CU11 que ya usa catalogo-page) y enlaza
        // cada colección a '/catalogo?coleccion_id=X', el mismo filtro que ya
        // usa el hero de colección destacada del Home -- sin IDs ni nombres
        // fijos en el código.
        path: 'colecciones',
        loadComponent: () =>
          import('./features/public/colecciones/colecciones-page/colecciones-page').then(
            (m) => m.ColeccionesPage,
          ),
        title: 'Colecciones · Fashion Store',
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
        // CU32 -- Gestionar promociones.
        path: 'promociones',
        loadComponent: () =>
          import('./features/admin/promociones/promociones').then((m) => m.Promociones),
        title: 'Promociones · Fashion Store Admin',
        data: {
          headerTitle: 'Promociones',
          headerSubtitle: 'Gestiona los descuentos porcentuales sobre productos del catálogo.',
        },
      },
      {
        // CU30 -- Consultar reportes e indicadores (primera parte: dashboard
        // analítico, sin voz/IA todavía).
        path: 'reportes',
        loadComponent: () =>
          import('./features/admin/reportes-indicadores/reportes').then((m) => m.Reportes),
        title: 'Reportes e indicadores · Fashion Store Admin',
        data: {
          headerTitle: 'Reportes e indicadores',
          headerSubtitle: 'Visión global de FashionStore para la toma de decisiones.',
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
  {
    path: 'encargado',
    loadComponent: () =>
      import('./layouts/encargado-layout/encargado-layout').then((m) => m.EncargadoLayout),
    canActivate: [authGuard, roleGuard('ENCARGADO_SUCURSAL')],
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadComponent: () => import('./features/encargado/inicio/inicio').then((m) => m.Inicio),
        title: 'Panel de Encargado · Fashion Store',
        data: {
          headerTitle: 'Panel de Encargado de Sucursal',
          headerSubtitle: '',
        },
      },
      {
        // CU14 -- Consultar inventario. Hereda el guard del padre
        // (authGuard + roleGuard('ENCARGADO_SUCURSAL')); el backend además
        // resuelve la sucursal siempre desde el usuario autenticado (ver
        // CU14_ConsultarInventario/router.py), nunca desde esta ruta.
        path: 'inventario',
        loadComponent: () =>
          import('./features/encargado/inventario/inventario').then((m) => m.Inventario),
        title: 'Inventario · Fashion Store Encargado',
        data: {
          headerTitle: 'Inventario',
          headerSubtitle: 'Consulta y ajusta el stock de tu sucursal.',
        },
      },
      {
        // CU15 -- Registrar recepción de mercadería. Hereda el guard del
        // padre (authGuard + roleGuard('ENCARGADO_SUCURSAL')); el backend
        // además resuelve la sucursal siempre desde el usuario autenticado
        // (ver CU15_RegistrarRecepcionMercaderia/router.py), nunca desde
        // esta ruta.
        path: 'recepcion-mercaderia',
        loadComponent: () =>
          import('./features/encargado/recepcion-mercaderia/recepcion-mercaderia').then(
            (m) => m.RecepcionMercaderia,
          ),
        title: 'Recepción de mercadería · Fashion Store Encargado',
        data: {
          headerTitle: 'Recepción de mercadería',
          headerSubtitle: 'Registra la mercadería recibida de un proveedor en tu sucursal.',
        },
      },
      {
        // CU16 -- Registrar movimientos de inventario. Hereda el guard del
        // padre (authGuard + roleGuard('ENCARGADO_SUCURSAL')); el backend
        // además resuelve la sucursal siempre desde el usuario autenticado
        // (ver CU16_RegistrarMovimientosInventario/router.py), nunca desde
        // esta ruta. Distinto de CU15 (recepción de proveedor): aquí son
        // ajustes manuales justificados, positivos o negativos.
        path: 'movimientos-inventario',
        loadComponent: () =>
          import('./features/encargado/movimientos-inventario/movimientos-inventario').then(
            (m) => m.MovimientosInventario,
          ),
        title: 'Movimientos de inventario · Fashion Store Encargado',
        data: {
          headerTitle: 'Movimientos de inventario',
          headerSubtitle: 'Registra ajustes manuales y justificados de stock en tu sucursal.',
        },
      },
      {
        // CU20 -- Atender reserva de prendas. Hereda el guard del padre
        // (authGuard + roleGuard('ENCARGADO_SUCURSAL')); el backend además
        // resuelve la sucursal siempre desde el usuario autenticado (ver
        // CU20_AtenderReservaPrendas/router.py), nunca desde esta ruta.
        path: 'reservas',
        loadComponent: () =>
          import('./features/encargado/reservas/reservas').then((m) => m.Reservas),
        title: 'Reservas · Fashion Store Encargado',
        data: {
          headerTitle: 'Reservas',
          headerSubtitle: 'Gestiona las reservas de prendas de tu sucursal.',
        },
      },
      {
        // Mismo componente MiPerfil de CU04 que ya usan '/mi-perfil' (Cliente)
        // y '/proveedor/mi-perfil' (Proveedor) -- sin duplicar el formulario,
        // solo registrado bajo el layout de Encargado para que nunca lo saque
        // de este árbol de rutas hacia el layout público.
        path: 'mi-perfil',
        loadComponent: () =>
          import('./usuarios-y-accesos/cu04-actualizar-perfil/mi-perfil').then((m) => m.MiPerfil),
        title: 'Mi perfil · Fashion Store Encargado',
        data: {
          headerTitle: 'Mi perfil',
          headerSubtitle: 'Datos de tu cuenta de Encargado de Sucursal.',
        },
      },
    ],
  },
  {
    // CAJERO -- panel completo con sidebar (mismo criterio visual que
    // EncargadoLayout, ver layouts/cajero-layout). Agrupa Inicio, CU24
    // (Ventas), CU20 (Reservas para caja -- antes en 'cajero' directo,
    // ahora 'cajero/reservas-pendientes'), CU26 (Devoluciones y cambios) y
    // Mi perfil bajo una sola navegación persistente.
    path: 'cajero',
    loadComponent: () =>
      import('./layouts/cajero-layout/cajero-layout').then((m) => m.CajeroLayout),
    canActivate: [authGuard, roleGuard('CAJERO')],
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadComponent: () => import('./features/cajero/inicio/inicio').then((m) => m.Inicio),
        title: 'Panel de Cajero · Fashion Store',
        data: {
          headerTitle: 'Panel de Cajero',
          headerSubtitle: '',
        },
      },
      {
        // CU24 -- Registrar venta presencial (Cajero), flujo A: venta
        // directa. A la que lleva "Ventas" del sidebar.
        path: 'ventas/nueva',
        loadComponent: () =>
          import('./features/cajero/ventas/venta-directa/venta-directa').then(
            (m) => m.VentaDirecta,
          ),
        title: 'Nueva venta · Fashion Store Cajero',
        data: {
          headerTitle: 'Nueva venta',
          headerSubtitle: 'Busca las prendas y arma la venta directa.',
        },
      },
      {
        // CU20 -- integración mínima con el rol Cajero: consulta de solo
        // lectura de las reservas que el Encargado ya dejó LISTA_PARA_CAJA
        // en SU sucursal (resuelta siempre del token en el backend).
        // "Cargar venta" (CU25) abre un modal sobre esta misma pantalla --
        // no navega, no tiene ruta propia.
        path: 'reservas-pendientes',
        loadComponent: () =>
          import('./features/cajero/reservas-pendientes/reservas-pendientes').then(
            (m) => m.ReservasPendientes,
          ),
        title: 'Reservas para caja · Fashion Store Cajero',
        data: {
          headerTitle: 'Reservas para caja',
          headerSubtitle: 'Reservas que tu sucursal ya dejó listas para continuar el proceso.',
        },
      },
      {
        // CU27 -- Consultar historial de compras (Cajero). Ítem propio
        // "Historial" del sidebar, separado de "Ventas" y "Devoluciones y
        // cambios" a propósito (requerimiento explícito: no mezclarlo con
        // Ventas).
        path: 'historial',
        loadComponent: () =>
          import('./features/cajero/historial/historial').then((m) => m.Historial),
        title: 'Historial · Fashion Store Cajero',
        data: {
          headerTitle: 'Historial',
          headerSubtitle: 'Ventas realizadas en tu sucursal.',
        },
      },
      {
        // CU26 -- Registrar devolución o cambio.
        path: 'devoluciones',
        loadComponent: () =>
          import('./features/cajero/devoluciones-cambios/devoluciones-cambios').then(
            (m) => m.DevolucionesCambios,
          ),
        title: 'Devoluciones y cambios · Fashion Store Cajero',
        data: {
          headerTitle: 'Devoluciones y cambios',
          headerSubtitle: 'Gestiona prendas de ventas realizadas.',
        },
      },
      {
        // CU31 -- Emitir comprobante de venta (Cajero). A la que navega
        // "Ver" del paso "PAGO REGISTRADO" de procesar-pago.ts (CU25) --
        // sin ítem propio en el sidebar (se llega desde el flujo de pago,
        // no es una sección de navegación aparte).
        path: 'comprobante/:ventaId',
        loadComponent: () =>
          import('./features/cajero/comprobantes/comprobante-cajero').then(
            (m) => m.ComprobanteCajero,
          ),
        title: 'Comprobante · Fashion Store Cajero',
        data: {
          headerTitle: 'Comprobante',
          headerSubtitle: 'Detalle de la venta ya pagada.',
        },
      },
      {
        // Mismo componente MiPerfil de CU04 que ya usan '/mi-perfil'
        // (Cliente), '/encargado/mi-perfil' y '/proveedor/mi-perfil' -- sin
        // duplicar el formulario.
        path: 'mi-perfil',
        loadComponent: () =>
          import('./usuarios-y-accesos/cu04-actualizar-perfil/mi-perfil').then((m) => m.MiPerfil),
        title: 'Mi perfil · Fashion Store Cajero',
        data: {
          headerTitle: 'Mi perfil',
          headerSubtitle: 'Datos de tu cuenta de Cajero.',
        },
      },
    ],
  },
  {
    // Ruta de nivel superior, sin ningún layout (admin/encargado/proveedor/
    // cajero/público): roleGuard() la usa para cualquier rol autenticado que
    // no coincide con la ruta pedida, y login.ts para un rol que no esté en
    // RUTA_POR_ROL (no debería ocurrir, pero nunca cae a un panel por
    // defecto) -- ver core/pages/no-autorizado/no-autorizado.ts.
    path: 'no-autorizado',
    loadComponent: () =>
      import('./core/pages/no-autorizado/no-autorizado').then((m) => m.NoAutorizado),
    title: 'Acceso no autorizado · Fashion Store',
  },
  { path: '**', redirectTo: '' },
];
