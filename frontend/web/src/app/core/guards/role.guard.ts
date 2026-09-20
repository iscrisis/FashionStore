import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { RolUsuario } from '../../usuarios-y-accesos/shared/models/usuario.model';
import { AuthService } from '../services/auth.service';

/**
 * Requiere sesión iniciada Y uno de los roles indicados.
 * Ejemplo: canActivate: [roleGuard('ADMINISTRADOR')]
 *
 * Un rol autenticado que no coincide con los indicados va a
 * '/no-autorizado', NUNCA a '/' (el layout público) -- ese fallback a '/'
 * era parte del mismo problema de arquitectura de roles ya corregido en
 * login.ts: terminar en el layout público es indistinguible de la
 * experiencia de un Cliente, sin importar si llegó ahí por la redirección
 * post-login o por navegar manualmente a una ruta de otro rol.
 */
export function roleGuard(...roles: RolUsuario[]): CanActivateFn {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    if (!auth.isAuthenticated()) {
      return router.createUrlTree(['/login']);
    }
    if (!auth.hasRole(...roles)) {
      return router.createUrlTree(['/no-autorizado']);
    }
    return true;
  };
}
