import { Component, inject, input, output, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { Icon } from '../../../core/ui/icon/icon';

@Component({
  selector: 'app-superadmin-header',
  imports: [Icon],
  templateUrl: './superadmin-header.html',
  styleUrl: './superadmin-header.scss',
})
export class SuperadminHeader {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly title = input('Dashboard');
  readonly subtitle = input('');
  readonly menuToggle = output<void>();

  protected readonly usuario = this.authService.usuario;
  protected readonly menuOpen = signal(false);

  protected get iniciales(): string {
    const nombre = this.usuario()?.nombre ?? '';
    return nombre.charAt(0).toUpperCase() || 'S';
  }

  toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  closeMenu(): void {
    this.menuOpen.set(false);
  }

  logout(): void {
    this.authService.logout();
    this.router.navigateByUrl('/');
  }
}
