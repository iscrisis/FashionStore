import { Component, ElementRef, HostListener, OnInit, inject, signal, viewChild } from '@angular/core';
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

  // Scroll horizontal SOLO visible/activo en móvil (ver category-section.scss)
  // -- en desktop/tablet la sección sigue siendo un grid normal, sin overflow,
  // así que estas flechas quedan ocultas por CSS y nunca se disparan.
  private readonly scrollContainer = viewChild<ElementRef<HTMLElement>>('scrollContainer');

  protected readonly canScrollLeft = signal(false);
  protected readonly canScrollRight = signal(false);

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
        // Espera a que Angular pinte las cards antes de medir scrollWidth.
        queueMicrotask(() => this.actualizarEstadoScroll());
      },
      error: () => {
        this.loading.set(false);
        this.hasError.set(true);
      },
    });
  }

  protected onScrollCategorias(): void {
    this.actualizarEstadoScroll();
  }

  @HostListener('window:resize')
  protected onResize(): void {
    this.actualizarEstadoScroll();
  }

  /** Desplaza una "página" (casi el ancho visible) hacia la izquierda (-1) o
   * derecha (1) -- nunca automático, solo se llama desde clic en flecha (ver
   * category-section.html). Sin loop: al llegar a un extremo, scrollBy deja
   * de avanzar más allá del scrollWidth real del navegador. */
  protected desplazar(direccion: -1 | 1): void {
    const el = this.scrollContainer()?.nativeElement;
    if (!el) {
      return;
    }
    el.scrollBy({ left: direccion * el.clientWidth * 0.85, behavior: 'smooth' });
  }

  private actualizarEstadoScroll(): void {
    const el = this.scrollContainer()?.nativeElement;
    if (!el) {
      this.canScrollLeft.set(false);
      this.canScrollRight.set(false);
      return;
    }
    const maxScroll = el.scrollWidth - el.clientWidth;
    this.canScrollLeft.set(el.scrollLeft > 4);
    this.canScrollRight.set(el.scrollLeft < maxScroll - 4);
  }
}
