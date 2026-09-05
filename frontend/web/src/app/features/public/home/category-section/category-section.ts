import { Component, OnInit, inject, signal } from '@angular/core';
import { Category } from '../../../../sucursales-catalogo/atributos/models/category.model';
import { CategoryService } from '../../../../sucursales-catalogo/atributos/services/category.service';
import { CategoryCard } from '../category-card/category-card';

@Component({
  selector: 'app-category-section',
  imports: [CategoryCard],
  templateUrl: './category-section.html',
  styleUrl: './category-section.scss',
})
export class CategorySection implements OnInit {
  private readonly categoryService = inject(CategoryService);

  protected readonly categories = signal<Category[]>([]);
  protected readonly loading = signal(true);
  protected readonly hasError = signal(false);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.hasError.set(false);
    // Solo se muestran las categorías ACTIVAS, administradas en /admin/catalogo/atributos (CU09).
    this.categoryService.list({ status: 'active' }).subscribe({
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
