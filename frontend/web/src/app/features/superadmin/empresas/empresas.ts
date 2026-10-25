import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { SuperadminService, Empresa } from '../services/superadmin.service';
import { Icon } from '../../../core/ui/icon/icon';

@Component({
  selector: 'app-superadmin-empresas',
  imports: [CommonModule, RouterLink, Icon],
  templateUrl: './empresas.html',
  styleUrl: './empresas.scss',
  standalone: true,
})
export class SuperadminEmpresas implements OnInit {
  private readonly superadminService = inject(SuperadminService);
  private readonly router = inject(Router);

  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly empresas = signal<Empresa[]>([]);

  ngOnInit(): void {
    this.cargarEmpresas();
  }

  private cargarEmpresas(): void {
    this.loading.set(true);
    this.error.set(null);
    this.superadminService.getEmpresas().subscribe({
      next: (data) => {
        this.empresas.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar las empresas.');
        this.loading.set(false);
      },
    });
  }

  verDetalle(empresa: Empresa): void {
    this.router.navigate(['/superadmin/empresas', empresa.id, 'administrador']);
  }

  reintentar(): void {
    this.cargarEmpresas();
  }
}
