import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { RolUsuario } from '../../usuarios-y-accesos/shared/models/usuario.model';
import { AuthService } from '../services/auth.service';

/**
 * Requiere sesión iniciada Y uno de los roles indicados.
 * Ejemplo: canActivate: [roleGuard('ADMINISTRADOR')]
 */
export function roleGuard(...roles: RolUsuario[]): CanActivateFn {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    if (!auth.isAuthenticated()) {
      return router.createUrlTree(['/login']);
    }
    if (!auth.hasRole(...roles)) {
      return router.createUrlTree(['/']);
    }
    return true;
  };
}
