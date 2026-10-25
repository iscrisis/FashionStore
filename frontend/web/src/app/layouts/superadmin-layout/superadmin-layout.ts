import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { SuperadminHeader } from './superadmin-header/superadmin-header';
import { SuperadminSidebar } from './superadmin-sidebar/superadmin-sidebar';

@Component({
  selector: 'app-superadmin-layout',
  imports: [RouterOutlet, SuperadminSidebar, SuperadminHeader],
  templateUrl: './superadmin-layout.html',
  styleUrl: './superadmin-layout.scss',
})
export class SuperadminLayout {
  private readonly router = inject(Router);
  private readonly activatedRoute = inject(ActivatedRoute);

  protected readonly headerTitle = signal('Dashboard');
  protected readonly headerSubtitle = signal('');
  protected readonly sidebarOpen = signal(false);

  constructor() {
    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => {
        this.readHeaderFromRoute();
        this.sidebarOpen.set(false);
      });
    this.readHeaderFromRoute();
  }

  toggleSidebar(): void {
    this.sidebarOpen.update((open) => !open);
  }

  closeSidebar(): void {
    this.sidebarOpen.set(false);
  }

  private readHeaderFromRoute(): void {
    let route = this.activatedRoute.firstChild;
    while (route?.firstChild) {
      route = route.firstChild;
    }
    const data = route?.snapshot?.data ?? {};
    this.headerTitle.set(data['headerTitle'] ?? 'Dashboard');
    this.headerSubtitle.set(data['headerSubtitle'] ?? '');
  }
}
