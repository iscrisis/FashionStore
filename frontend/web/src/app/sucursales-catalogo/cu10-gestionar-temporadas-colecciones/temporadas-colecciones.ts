import { Component, signal } from '@angular/core';
import { ColeccionManagement } from './coleccion-management/coleccion-management';
import { TemporadaManagement } from './temporada-management/temporada-management';

type CatalogTab = 'temporadas' | 'colecciones';

@Component({
  selector: 'app-temporadas-colecciones',
  imports: [TemporadaManagement, ColeccionManagement],
  templateUrl: './temporadas-colecciones.html',
  styleUrl: './temporadas-colecciones.scss',
})
export class TemporadasColecciones {
  protected readonly activeTab = signal<CatalogTab>('temporadas');

  setTab(tab: CatalogTab): void {
    this.activeTab.set(tab);
  }
}
