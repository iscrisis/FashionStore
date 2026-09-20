import { Component, inject, input, output } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { Icon } from '../../../core/ui/icon/icon';

@Component({
  selector: 'app-cajero-header',
  imports: [Icon],
  templateUrl: './cajero-header.html',
  styleUrl: './cajero-header.scss',
})
export class CajeroHeader {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly title = input('Panel de Cajero');
  readonly subtitle = input('');

  // Botón hamburguesa -- visible solo en tablet/móvil (ver
  // cajero-header.scss), abre el drawer del sidebar (CajeroLayout).
  readonly abrirMenu = output<void>();

  protected readonly usuario = this.authService.usuario;

  protected get iniciales(): string {
    const nombre = this.usuario()?.nombre ?? '';
    return nombre.charAt(0).toUpperCase() || 'C';
  }

  logout(): void {
    this.authService.logout();
    this.router.navigateByUrl('/');
  }
}
