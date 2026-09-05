import { Component, input } from '@angular/core';
import { Category } from '../../../../sucursales-catalogo/atributos/models/category.model';
import { Icon } from '../../../../core/ui/icon/icon';

@Component({
  selector: 'app-category-card',
  imports: [Icon],
  templateUrl: './category-card.html',
  styleUrl: './category-card.scss',
})
export class CategoryCard {
  readonly category = input.required<Category>();
}
