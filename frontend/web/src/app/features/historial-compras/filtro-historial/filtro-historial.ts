import { Component, computed, output, signal } from '@angular/core';
import { FiltroHistorial as FiltroHistorialQuery } from '../historial-compras.model';

/**
 * CU27 -- Consultar historial de compras. Barra de filtros PURA (sin fetch
 * propio) -- reutilizada tal cual por features/cliente/historial-compras y
 * features/cajero/historial, nunca duplicada. Las reglas ("Desde" y "Hasta"
 * son cada una opcional, y si ambas están, Desde <= Hasta) se validan aquí
 * SOLO para feedback inmediato -- la autoridad real, y el filtrado en sí,
 * siempre vive en FastAPI (ver CU27_ConsultarHistorialCompras/service.py).
 */
@Component({
  selector: 'app-filtro-historial',
  imports: [],
  templateUrl: './filtro-historial.html',
  styleUrl: './filtro-historial.scss',
})
export class FiltroHistorial {
  readonly filtrar = output<FiltroHistorialQuery>();

  protected readonly desde = signal('');
  protected readonly hasta = signal('');
  protected readonly codigo = signal('');

  protected readonly rangoInvalido = computed(() => {
    const desde = this.desde();
    const hasta = this.hasta();
    return !!desde && !!hasta && desde > hasta;
  });

  actualizarDesde(valor: string): void {
    this.desde.set(valor);
  }

  actualizarHasta(valor: string): void {
    this.hasta.set(valor);
  }

  actualizarCodigo(valor: string): void {
    this.codigo.set(valor.toUpperCase());
  }

  aplicar(): void {
    if (this.rangoInvalido()) {
      return;
    }
    this.filtrar.emit({
      desde: this.desde() || undefined,
      hasta: this.hasta() || undefined,
      codigo_venta: this.codigo().trim() || undefined,
    });
  }

  limpiar(): void {
    this.desde.set('');
    this.hasta.set('');
    this.codigo.set('');
    this.filtrar.emit({});
  }
}
