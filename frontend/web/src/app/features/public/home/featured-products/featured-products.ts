import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ProductoPublico } from '../../catalogo/catalogo.model';
import { CatalogoService } from '../../catalogo/catalogo.service';
import { AuthService } from '../../../../core/services/auth.service';
import { ProductCard } from '../product-card/product-card';

const MAX_DESTACADOS = 8;

@Component({
  selector: 'app-featured-products',
  imports: [ProductCard, RouterLink],
  templateUrl: './featured-products.html',
  styleUrl: './featured-products.scss',
})
export class FeaturedProducts implements OnInit {
  private readonly catalogoService = inject(CatalogoService);
  private readonly authService = inject(AuthService);

  protected readonly products = signal<ProductoPublico[]>([]);
  protected readonly loading = signal(true);
  protected readonly hasError = signal(false);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.hasError.set(false);
    const usuario = this.authService.usuario();
    this.catalogoService.listProductos({ empresa_id: usuario?.empresa_id }).subscribe({
      next: (productos) => {
        this.products.set(productos.slice(0, MAX_DESTACADOS));
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.hasError.set(true);
      },
    });
  }
}
