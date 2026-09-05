import { Component, effect, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { resolveMediaUrl } from '../../../../core/utils/resolve-media-url';
import { Icon } from '../../../../core/ui/icon/icon';
import { ProductoPublico } from '../../catalogo/catalogo.model';

@Component({
  selector: 'app-product-card',
  imports: [Icon, RouterLink],
  templateUrl: './product-card.html',
  styleUrl: './product-card.scss',
})
export class ProductCard {
  readonly product = input.required<ProductoPublico>();

  protected readonly resolveMediaUrl = resolveMediaUrl;
  protected readonly imageError = signal(false);

  // Estado puramente visual: la lógica real de favoritos llegará con su propio caso de uso.
  protected readonly isFavorite = signal(false);

  constructor() {
    // Si la imagen referenciada ya no existe físicamente (ej. archivo perdido),
    // el navegador dispara (error) -- se cae al ícono, nunca al roto nativo.
    effect(() => {
      this.product();
      this.imageError.set(false);
    });
  }

  toggleFavorite(event: Event): void {
    event.preventDefault();
    this.isFavorite.update((value) => !value);
  }
}
