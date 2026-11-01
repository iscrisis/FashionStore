import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AsistenteIa } from '../../features/cliente/asistente-ia/asistente-ia';
import { PublicHeader } from './public-header/public-header';
import { AuthService } from '../../core/services/auth.service';
import { SuperadminService } from '../../features/superadmin/services/superadmin.service';

@Component({
  selector: 'app-public-layout',
  imports: [RouterOutlet, PublicHeader, AsistenteIa],
  templateUrl: './public-layout.html',
  styleUrl: './public-layout.scss',
})
export class PublicLayout implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly superadminService = inject(SuperadminService);

  protected readonly tieneFuncionialidadIA = signal(false);

  ngOnInit(): void {
    const usuario = this.authService.usuario();
    if (usuario?.empresa_id) {
      this.superadminService.getSuscripcionEmpresa(usuario.empresa_id).subscribe({
        next: (data: any) => {
          const tieneFuncionialidad = data.plan?.reportes_generativos_ia ?? false;
          this.tieneFuncionialidadIA.set(tieneFuncionialidad);
        },
        error: () => this.tieneFuncionialidadIA.set(false),
      });
    }
  }
}
