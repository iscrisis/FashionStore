import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { RUTA_POR_ROL } from '../../utils/ruta-por-rol';

/**
 * Página genérica de "Acceso no autorizado" -- corrige el problema de
 * arquitectura de roles: antes, un rol sin una ruta propia (o un rol que
 * `roleGuard` rechaza para la ruta actual) terminaba silenciosamente en '/'
 * (el layout público), indistinguible de la experiencia de un Cliente. Ver
 * role.guard.ts (usa esta ruta en vez de '/') y
 * cu01-iniciar-sesion/login.ts (mismo destino si el rol del usuario
 * autenticado no coincide con ninguno de los 5 roles conocidos).
 *
 * No pertenece a ningún layout (admin/encargado/proveedor/cajero/público):
 * es una ruta de nivel superior sin sidebar ni header propios, porque puede
 * mostrarse para cualquier rol o incluso sin rol reconocible.
 */
@Component({
  selector: 'app-no-autorizado',
  templateUrl: './no-autorizado.html',
  styleUrl: './no-autorizado.scss',
})
export class NoAutorizado {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  // Si la sesión tiene un rol reconocido, vuelve a SU propio panel (no a la
  // ruta que le fue negada) -- así un Encargado que cae aquí por navegar a
  // /admin, por ejemplo, no queda varado. Sin sesión o con un rol que no
  // está en el mapa, la única salida razonable es volver a iniciar sesión.
  volver(): void {
    const rol = this.authService.usuario()?.rol;
    const destino = rol ? RUTA_POR_ROL[rol] : undefined;
    if (destino) {
      this.router.navigateByUrl(destino);
      return;
    }
    this.authService.logout();
    this.router.navigateByUrl('/login');
  }
}
