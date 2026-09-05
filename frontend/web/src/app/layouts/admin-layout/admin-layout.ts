import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { AdminHeader } from './admin-header/admin-header';
import { AdminSidebar } from './admin-sidebar/admin-sidebar';

@Component({
  selector: 'app-admin-layout',
  imports: [RouterOutlet, AdminSidebar, AdminHeader],
  templateUrl: './admin-layout.html',
  styleUrl: './admin-layout.scss',
})
export class AdminLayout {
  private readonly router = inject(Router);
  private readonly activatedRoute = inject(ActivatedRoute);

  protected readonly headerTitle = signal('Panel de administración');
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
    this.headerTitle.set(data['headerTitle'] ?? 'Panel de administración');
    this.headerSubtitle.set(data['headerSubtitle'] ?? '');
  }
}
