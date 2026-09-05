import { Component, input, signal } from '@angular/core';
import { Icon } from '../../../../core/ui/icon/icon';
import { MockProduct } from '../featured-products/mock-product.model';

@Component({
  selector: 'app-product-card',
  imports: [Icon],
  templateUrl: './product-card.html',
  styleUrl: './product-card.scss',
})
export class ProductCard {
  readonly product = input.required<MockProduct>();

  // Estado puramente visual: la lógica real de favoritos llegará con su propio caso de uso.
  protected readonly isFavorite = signal(false);

  toggleFavorite(event: Event): void {
    event.preventDefault();
    this.isFavorite.update((value) => !value);
  }
}
