import { Component, signal } from '@angular/core';
import { CategoryManagement } from './category-management/category-management';
import { ColorManagement } from './color-management/color-management';
import { SizeManagement } from './size-management/size-management';

type CatalogTab = 'categories' | 'sizes' | 'colors';

@Component({
  selector: 'app-catalog-attributes',
  imports: [CategoryManagement, SizeManagement, ColorManagement],
  templateUrl: './catalog-attributes.html',
  styleUrl: './catalog-attributes.scss',
})
export class CatalogAttributes {
  protected readonly activeTab = signal<CatalogTab>('categories');

  setTab(tab: CatalogTab): void {
    this.activeTab.set(tab);
  }
}
