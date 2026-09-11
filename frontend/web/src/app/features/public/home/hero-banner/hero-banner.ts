import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { environment } from '../../../../../environments/environment';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';

interface ColeccionDestacada {
  id: number;
  imagen_destacada_url: string | null;
}

@Component({
  selector: 'app-hero-banner',
  imports: [RouterLink],
  templateUrl: './hero-banner.html',
  styleUrl: './hero-banner.scss',
})
export class HeroBanner {
  private readonly http = inject(HttpClient);

  // La colección destacada se gestiona desde CU10 (Admin > Temporadas y
  // colecciones); este componente solo la consume vía el endpoint público
  // /colecciones/destacada. Si no hay ninguna marcada (o falla la carga), el
  // hero se queda con el texto estático y sin imagen/CTA -- nunca rompe.
  protected readonly coleccionDestacada = signal<ColeccionDestacada | null>(null);
  protected readonly resolveMediaUrl = resolveMediaUrl;

  constructor() {
    this.http
      .get<ColeccionDestacada | null>(`${environment.apiUrl}/colecciones/destacada`)
      .subscribe({
        next: (coleccion) => this.coleccionDestacada.set(coleccion),
        error: () => this.coleccionDestacada.set(null),
      });
  }
}
