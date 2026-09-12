import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { Icon } from '../../../core/ui/icon/icon';

interface PublicNavLink {
  label: string;
  path: string;
  fragment?: string;
}

@Component({
  selector: 'app-public-header',
  imports: [Icon, RouterLink],
  templateUrl: './public-header.html',
  styleUrl: './public-header.scss',
})
export class PublicHeader {
  protected readonly authService = inject(AuthService);

  // Cada entrada apunta a una vista/sección real: "Categorías" lleva a la
  // sección "Compra por categorías" del Home (id="categorias") y
  // "Colecciones" reutiliza el catálogo (CU11), donde ya existe un filtro con
  // las colecciones reales de CU10.
  protected readonly navLinks: PublicNavLink[] = [
    { label: 'Inicio', path: '/' },
    { label: 'Catálogo', path: '/catalogo' },
    { label: 'Categorías', path: '/', fragment: 'categorias' },
    { label: 'Colecciones', path: '/catalogo' },
  ];

  protected readonly mobileMenuOpen = signal(false);
  // Sin CU de carrito todavía: 0 real, no una cifra inventada.
  protected readonly cartCount = signal(0);

  toggleMobileMenu(): void {
    this.mobileMenuOpen.update((open) => !open);
  }

  closeMobileMenu(): void {
    this.mobileMenuOpen.set(false);
  }

  protected get destinoCuenta(): string {
    // CU04 -- Actualizar perfil: el CLIENTE va a "Mi perfil" (sigue dentro de
    // la tienda pública, no es un panel). ADMINISTRADOR conserva su acceso
    // directo al panel de administración, sin tocar esa lógica.
    if (this.authService.hasRole('ADMINISTRADOR')) {
      return '/admin';
    }
    if (this.authService.hasRole('CLIENTE')) {
      return '/mi-perfil';
    }
    return '/';
  }
}
