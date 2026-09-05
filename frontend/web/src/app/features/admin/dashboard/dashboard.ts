import { Component, inject, signal } from '@angular/core';
import { AuthService } from '../../../core/services/auth.service';
import { Icon } from '../../../core/ui/icon/icon';
import { UsuarioAdminService } from '../../../usuarios-y-accesos/cu05-gestionar-usuarios-roles/usuario-admin.service';

/**
 * Panel de inicio del administrador. Los únicos datos reales disponibles hoy
 * provienen de CU05 (usuarios y roles); no se inventan estadísticas de
 * módulos que todavía no existen (sucursales, productos, reservas, ventas).
 */
@Component({
  selector: 'app-dashboard',
  imports: [Icon],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard {
  private readonly usuarioService = inject(UsuarioAdminService);
  protected readonly authService = inject(AuthService);

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly usuariosActivos = signal(0);
  protected readonly usuariosInactivos = signal(0);
  protected readonly rolesDisponibles = signal(0);

  constructor() {
    this.usuarioService.list().subscribe({
      next: (usuarios) => {
        this.usuariosActivos.set(usuarios.filter((u) => u.is_active).length);
        this.usuariosInactivos.set(usuarios.filter((u) => !u.is_active).length);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.errorMessage.set('No se pudieron cargar los datos de usuarios.');
      },
    });

    this.usuarioService.roles().subscribe({
      next: (roles) => this.rolesDisponibles.set(roles.length),
    });
  }
}
