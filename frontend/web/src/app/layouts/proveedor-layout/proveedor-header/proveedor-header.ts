import { Component, inject, input } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-proveedor-header',
  imports: [],
  templateUrl: './proveedor-header.html',
  styleUrl: './proveedor-header.scss',
})
export class ProveedorHeader {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly title = input('Panel de Proveedor');
  readonly subtitle = input('');

  protected readonly usuario = this.authService.usuario;

  protected get iniciales(): string {
    const nombre = this.usuario()?.nombre ?? '';
    return nombre.charAt(0).toUpperCase() || 'P';
  }

  logout(): void {
    this.authService.logout();
    this.router.navigateByUrl('/');
  }
}
