import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { Icon } from '../../../core/ui/icon/icon';

interface PublicNavLink {
  label: string;
  href: string;
}

@Component({
  selector: 'app-public-header',
  imports: [Icon, RouterLink],
  templateUrl: './public-header.html',
  styleUrl: './public-header.scss',
})
export class PublicHeader {
  protected readonly authService = inject(AuthService);

  // Navegación principal del sitio: NO proviene del CU09 (categorías del catálogo).
  // Se define aparte porque agrupa categorías, colecciones y ofertas con criterios propios.
  protected readonly navLinks: PublicNavLink[] = [
    { label: 'Mujer', href: '/' },
    { label: 'Hombre', href: '/' },
    { label: 'Niños', href: '/' },
    { label: 'Colecciones', href: '/' },
    { label: 'Ofertas', href: '/' },
    { label: 'Novedades', href: '/' },
  ];

  protected readonly mobileMenuOpen = signal(false);
  // Sin CU de carrito todavía: 0 real, no una cifra inventada.
  protected readonly cartCount = signal(0);

  toggleMobileMenu(): void {
    this.mobileMenuOpen.update((open) => !open);
  }

  protected get destinoCuenta(): string {
    return this.authService.hasRole('ADMINISTRADOR') ? '/admin' : '/';
  }
}
