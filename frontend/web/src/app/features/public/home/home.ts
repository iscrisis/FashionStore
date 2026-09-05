import { Component } from '@angular/core';
import { CategorySection } from './category-section/category-section';
import { FeaturedProducts } from './featured-products/featured-products';
import { HeroBanner } from './hero-banner/hero-banner';

@Component({
  selector: 'app-home',
  imports: [HeroBanner, CategorySection, FeaturedProducts],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {}
