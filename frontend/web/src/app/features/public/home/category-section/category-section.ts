import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CategoriaPublica } from '../../catalogo/catalogo.model';
import { CatalogoService } from '../../catalogo/catalogo.service';
import { CategoryCard } from '../category-card/category-card';

@Component({
  selector: 'app-category-section',
  imports: [CategoryCard, RouterLink],
  templateUrl: './category-section.html',
  styleUrl: './category-section.scss',
})
export class CategorySection implements OnInit {
  private readonly catalogoService = inject(CatalogoService);

  protected readonly categories = signal<CategoriaPublica[]>([]);
  protected readonly loading = signal(true);
  protected readonly hasError = signal(false);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.hasError.set(false);
    // CU11 (catálogo público): solo categorías ACTIVAS, sin requerir sesión.
    this.catalogoService.listCategorias().subscribe({
      next: (categories) => {
        this.categories.set(categories);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.hasError.set(true);
      },
    });
  }
}
