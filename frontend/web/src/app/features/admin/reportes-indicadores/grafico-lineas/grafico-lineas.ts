import { Component, computed, input } from '@angular/core';

export interface PuntoLinea {
  etiqueta: string;
  valor: number;
}

const ANCHO = 600;
const ALTO = 160;
const PADDING = 8;

/**
 * CU30 -- gráfico de tendencia (línea + área), SVG puro con viewBox
 * (preserveAspectRatio="none" lo estira al ancho real del contenedor --
 * responsive sin media queries propias). Usado por "Ventas por periodo"
 * (ver reportes.ts) -- sin librería de gráficos nueva.
 */
@Component({
  selector: 'app-grafico-lineas',
  templateUrl: './grafico-lineas.html',
  styleUrl: './grafico-lineas.scss',
})
export class GraficoLineas {
  readonly puntos = input.required<PuntoLinea[]>();

  protected readonly viewBox = `0 0 ${ANCHO} ${ALTO}`;

  private readonly maximo = computed(() => Math.max(1, ...this.puntos().map((p) => p.valor)));
  private readonly minimo = computed(() => Math.min(0, ...this.puntos().map((p) => p.valor)));

  private readonly coordenadas = computed(() => {
    const datos = this.puntos();
    if (datos.length === 0) {
      return [] as { x: number; y: number }[];
    }
    const max = this.maximo();
    const min = this.minimo();
    const rango = max - min || 1;
    const pasoX = datos.length > 1 ? (ANCHO - PADDING * 2) / (datos.length - 1) : 0;
    return datos.map((punto, indice) => ({
      x: PADDING + indice * pasoX,
      y: ALTO - PADDING - ((punto.valor - min) / rango) * (ALTO - PADDING * 2),
    }));
  });

  protected readonly puntosSvg = computed(() =>
    this.coordenadas()
      .map((c) => `${c.x.toFixed(1)},${c.y.toFixed(1)}`)
      .join(' '),
  );

  protected readonly areaSvg = computed(() => {
    const coords = this.coordenadas();
    if (coords.length === 0) {
      return '';
    }
    const base = ALTO - PADDING;
    const primero = coords[0];
    const ultimo = coords[coords.length - 1];
    return `${primero.x.toFixed(1)},${base} ${this.puntosSvg()} ${ultimo.x.toFixed(1)},${base}`;
  });

  protected readonly primerEtiqueta = computed(() => this.puntos()[0]?.etiqueta ?? '');
  protected readonly ultimaEtiqueta = computed(() => this.puntos().at(-1)?.etiqueta ?? '');
}
