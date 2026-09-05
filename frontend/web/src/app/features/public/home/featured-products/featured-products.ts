import { Component } from '@angular/core';
import { ProductCard } from '../product-card/product-card';
import { MockProduct } from './mock-product.model';

@Component({
  selector: 'app-featured-products',
  imports: [ProductCard],
  templateUrl: './featured-products.html',
  styleUrl: './featured-products.scss',
})
export class FeaturedProducts {
  // Sin CU08 (gestionar productos) todavía no hay prendas reales que mostrar.
  // La estructura visual (grid + ProductCard) queda lista para cuando el
  // administrador empiece a publicar productos.
  protected readonly products: MockProduct[] = [];
}
