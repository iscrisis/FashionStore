import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-hero-banner',
  templateUrl: './hero-banner.html',
  styleUrl: './hero-banner.scss',
})
export class HeroBanner {
  // Slides decorativos — la fotografía real de campaña llegará con el CU de contenidos/promos.
  protected readonly slides = [0, 1, 2];
  protected readonly activeSlide = signal(0);
}
