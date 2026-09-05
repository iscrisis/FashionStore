import { Component, effect, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { CategoriaPublica } from '../../catalogo/catalogo.model';
import { Icon } from '../../../../core/ui/icon/icon';

@Component({
  selector: 'app-category-card',
  imports: [Icon, RouterLink],
  templateUrl: './category-card.html',
  styleUrl: './category-card.scss',
})
export class CategoryCard {
  readonly category = input.required<CategoriaPublica>();

  protected readonly resolveMediaUrl = resolveMediaUrl;
  protected readonly imageError = signal(false);

  constructor() {
    // Si la imagen referenciada ya no existe físicamente (ej. archivo perdido),
    // el navegador dispara (error) -- se cae al ícono, nunca al roto nativo.
    effect(() => {
      this.category();
      this.imageError.set(false);
    });
  }
}
