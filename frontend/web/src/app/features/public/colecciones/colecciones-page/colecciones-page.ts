import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ColeccionPublica } from '../../catalogo/catalogo.model';
import { CatalogoService } from '../../catalogo/catalogo.service';

/**
 * Vista pública de colecciones (CU10 -> vitrina de cliente/invitado).
 * Reutiliza el mismo endpoint público de catálogo que ya filtra por
 * colecciones activas (GET /catalogo/colecciones); no crea datos nuevos.
 */
@Component({
  selector: 'app-colecciones-page',
  imports: [RouterLink],
  templateUrl: './colecciones-page.html',
  styleUrl: './colecciones-page.scss',
})
export class ColeccionesPage {
  private readonly catalogoService = inject(CatalogoService);

  protected readonly colecciones = signal<ColeccionPublica[]>([]);
  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.catalogoService.listColecciones().subscribe({
      next: (valores) => {
        this.colecciones.set(valores);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.colecciones.set([]);
        this.errorMessage.set('No se pudo conectar con el servidor. Inténtalo nuevamente.');
      },
    });
  }
}
