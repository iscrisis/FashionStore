import { Component, computed, input } from '@angular/core';

export interface BarraItem {
  etiqueta: string;
  valor: number;
  // Texto ya formateado para mostrar (ej. "Bs 640.00") -- si no se da, se
  // muestra `valor` tal cual.
  valorTexto?: string;
}

/**
 * CU30 -- gráfico de barras horizontales, minimalista (SVG/CSS puro, sin
 * librería nueva -- ver instrucciones de CU30: "revisa package.json antes
 * de instalar cualquier librería de gráficos"). Reutilizado por varias
 * secciones del dashboard (ventas por tipo/método de pago/sucursal,
 * productos más vendidos) -- una sola implementación, sin duplicar el
 * cálculo de proporciones en cada sección.
 */
@Component({
  selector: 'app-grafico-barras',
  templateUrl: './grafico-barras.html',
  styleUrl: './grafico-barras.scss',
})
export class GraficoBarras {
  readonly items = input.required<BarraItem[]>();

  protected readonly maximo = computed(() => Math.max(1, ...this.items().map((item) => item.valor)));

  protected porcentaje(valor: number): number {
    return Math.max(2, Math.round((valor / this.maximo()) * 100));
  }
}
