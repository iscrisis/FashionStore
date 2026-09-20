import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

/**
 * "Inicio" del panel del Cajero -- pantalla de bienvenida mínima, mismo
 * criterio que features/encargado/inicio: sin datos propios que consultar,
 * solo accesos rápidos a las pantallas reales del rol (CU24 Ventas, CU20
 * Reservas para caja, CU26 Devoluciones y cambios).
 */
@Component({
  selector: 'app-cajero-inicio',
  imports: [RouterLink],
  templateUrl: './inicio.html',
  styleUrl: './inicio.scss',
})
export class Inicio {
  private readonly authService = inject(AuthService);

  protected readonly usuario = this.authService.usuario;
}
