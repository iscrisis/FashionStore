import { Component, inject, input, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { Icon } from '../../../core/ui/icon/icon';

@Component({
  selector: 'app-admin-header',
  imports: [Icon],
  templateUrl: './admin-header.html',
  styleUrl: './admin-header.scss',
})
export class AdminHeader {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly title = input('Panel de administración');
  readonly subtitle = input('');

  protected readonly usuario = this.authService.usuario;
  protected readonly menuOpen = signal(false);

  protected get iniciales(): string {
    const nombre = this.usuario()?.nombre ?? '';
    return nombre.charAt(0).toUpperCase() || 'A';
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
