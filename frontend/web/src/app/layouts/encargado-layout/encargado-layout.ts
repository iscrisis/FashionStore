import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { EncargadoHeader } from './encargado-header/encargado-header';
import { EncargadoSidebar } from './encargado-sidebar/encargado-sidebar';

@Component({
  selector: 'app-encargado-layout',
  imports: [RouterOutlet, EncargadoSidebar, EncargadoHeader],
  templateUrl: './encargado-layout.html',
  styleUrl: './encargado-layout.scss',
})
export class EncargadoLayout {
  private readonly router = inject(Router);
  private readonly activatedRoute = inject(ActivatedRoute);

  protected readonly headerTitle = signal('Panel de Encargado de Sucursal');
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
    this.headerTitle.set(data['headerTitle'] ?? 'Panel de Encargado de Sucursal');
    this.headerSubtitle.set(data['headerSubtitle'] ?? '');
  }
}
