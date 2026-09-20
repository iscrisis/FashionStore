import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { CajeroHeader } from './cajero-header/cajero-header';
import { CajeroSidebar } from './cajero-sidebar/cajero-sidebar';

/**
 * Panel completo del CAJERO (CU26) -- mismo criterio visual que
 * EncargadoLayout: sidebar fijo en escritorio, con la misma línea visual
 * (marca, navegación, header con título dinámico por ruta). A diferencia de
 * EncargadoLayout (que en pantallas angostas convierte el sidebar en una
 * franja horizontal siempre visible), aquí en tablet/móvil el sidebar se
 * oculta como un drawer deslizable, abierto con el botón hamburguesa del
 * header -- pedido explícito para el panel del Cajero, ver
 * cajero-layout.scss.
 */
@Component({
  selector: 'app-cajero-layout',
  imports: [RouterOutlet, CajeroSidebar, CajeroHeader],
  templateUrl: './cajero-layout.html',
  styleUrl: './cajero-layout.scss',
})
export class CajeroLayout {
  private readonly router = inject(Router);
  private readonly activatedRoute = inject(ActivatedRoute);

  protected readonly headerTitle = signal('Panel de Cajero');
  protected readonly headerSubtitle = signal('');
  protected readonly drawerAbierto = signal(false);

  constructor() {
    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => {
        this.readHeaderFromRoute();
        this.drawerAbierto.set(false);
      });
    this.readHeaderFromRoute();
  }

  abrirDrawer(): void {
    this.drawerAbierto.set(true);
  }

  cerrarDrawer(): void {
    this.drawerAbierto.set(false);
  }

  private readHeaderFromRoute(): void {
    let route = this.activatedRoute.firstChild;
    while (route?.firstChild) {
      route = route.firstChild;
    }
    const data = route?.snapshot?.data ?? {};
    this.headerTitle.set(data['headerTitle'] ?? 'Panel de Cajero');
    this.headerSubtitle.set(data['headerSubtitle'] ?? '');
  }
}
