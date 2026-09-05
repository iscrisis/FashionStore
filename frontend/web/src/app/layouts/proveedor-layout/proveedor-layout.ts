import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { ProveedorHeader } from './proveedor-header/proveedor-header';
import { ProveedorSidebar } from './proveedor-sidebar/proveedor-sidebar';

@Component({
  selector: 'app-proveedor-layout',
  imports: [RouterOutlet, ProveedorSidebar, ProveedorHeader],
  templateUrl: './proveedor-layout.html',
  styleUrl: './proveedor-layout.scss',
})
export class ProveedorLayout {
  private readonly router = inject(Router);
  private readonly activatedRoute = inject(ActivatedRoute);

  protected readonly headerTitle = signal('Panel de Proveedor');
  protected readonly headerSubtitle = signal('');

  constructor() {
    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => this.readHeaderFromRoute());
    this.readHeaderFromRoute();
  }

  private readHeaderFromRoute(): void {
    let route = this.activatedRoute.firstChild;
    while (route?.firstChild) {
      route = route.firstChild;
    }
    const data = route?.snapshot?.data ?? {};
    this.headerTitle.set(data['headerTitle'] ?? 'Panel de Proveedor');
    this.headerSubtitle.set(data['headerSubtitle'] ?? '');
  }
}
