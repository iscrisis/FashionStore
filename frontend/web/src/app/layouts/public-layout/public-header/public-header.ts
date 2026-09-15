import { Component, HostListener, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { Icon } from '../../../core/ui/icon/icon';

const ETIQUETAS_ROL: Record<string, string> = {
  ADMINISTRADOR: 'Administrador',
  ENCARGADO_SUCURSAL: 'Encargado de sucursal',
  CAJERO: 'Cajero',
  PROVEEDOR: 'Proveedor',
  CLIENTE: 'Cliente',
};

interface PublicNavLink {
  label: string;
  path: string;
  fragment?: string;
}

@Component({
  selector: 'app-public-header',
  imports: [Icon, RouterLink, RouterLinkActive],
  templateUrl: './public-header.html',
  styleUrl: './public-header.scss',
})
export class PublicHeader {
  protected readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  // Cada entrada apunta a una vista/sección real: "Categorías" lleva a la
  // sección "Compra por categorías" del Home (id="categorias") y
  // "Colecciones" lleva a la vitrina pública de colecciones (CU10), desde
  // donde el cliente entra al catálogo (CU11) ya filtrado por la colección.
  protected readonly navLinks: PublicNavLink[] = [
    { label: 'Inicio', path: '/' },
    { label: 'Catálogo', path: '/catalogo' },
    { label: 'Categorías', path: '/', fragment: 'categorias' },
    { label: 'Colecciones', path: '/colecciones' },
  ];

  protected readonly mobileMenuOpen = signal(false);
  protected readonly accountMenuOpen = signal(false);
  // Sin CU de carrito todavía: 0 real, no una cifra inventada.
  protected readonly cartCount = signal(0);

  toggleMobileMenu(): void {
    this.mobileMenuOpen.update((open) => !open);
  }

  closeMobileMenu(): void {
    this.mobileMenuOpen.set(false);
  }

  toggleAccountMenu(event: Event): void {
    event.stopPropagation();
    this.accountMenuOpen.update((open) => !open);
  }

  // Cierra el menú de cuenta al hacer clic en cualquier otro lugar de la
  // página (el botón que lo abre detiene la propagación, ver arriba).
  @HostListener('document:click')
  closeAccountMenu(): void {
    this.accountMenuOpen.set(false);
  }

  logout(): void {
    this.authService.logout();
    this.accountMenuOpen.set(false);
    this.router.navigateByUrl('/');
  }

  protected get destinoCuenta(): string {
    // CU04 -- Actualizar perfil: el CLIENTE va a "Mi perfil" (sigue dentro de
    // la tienda pública, no es un panel). ADMINISTRADOR conserva su acceso
    // directo al panel de administración, sin tocar esa lógica. ENCARGADO_SUCURSAL
    // nunca debe quedarse en el layout público: si este header llega a
    // mostrarse mientras tiene sesión (p. ej. navegó manualmente a una URL
    // pública), "Mi cuenta" lo manda de vuelta a su propio panel, no a Home.
    if (this.authService.hasRole('ADMINISTRADOR')) {
      return '/admin';
    }
    if (this.authService.hasRole('ENCARGADO_SUCURSAL')) {
      return '/encargado';
    }
    if (this.authService.hasRole('CLIENTE')) {
      return '/mi-perfil';
    }
    return '/';
  }

  protected get etiquetaCuenta(): string {
    return this.authService.hasRole('CLIENTE') ? 'Mi perfil' : 'Mi cuenta';
  }

  protected get etiquetaRol(): string {
    const rol = this.authService.usuario()?.rol;
    return rol ? (ETIQUETAS_ROL[rol] ?? rol) : '';
  }
}
