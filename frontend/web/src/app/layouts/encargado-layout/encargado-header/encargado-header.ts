import { Component, inject, input } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-encargado-header',
  imports: [],
  templateUrl: './encargado-header.html',
  styleUrl: './encargado-header.scss',
})
export class EncargadoHeader {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly title = input('Panel de Encargado de Sucursal');
  readonly subtitle = input('');

  protected readonly usuario = this.authService.usuario;

  protected get iniciales(): string {
    const nombre = this.usuario()?.nombre ?? '';
    return nombre.charAt(0).toUpperCase() || 'E';
  }

  logout(): void {
    this.authService.logout();
    this.router.navigateByUrl('/');
  }
}
