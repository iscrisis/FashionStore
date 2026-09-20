import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { VentaPresencialOut } from '../venta-presencial.model';
import { VentaResumen } from './venta-resumen';

/**
 * Prueba de regresión para CU24 -- resumen de venta presencial (venta
 * DIRECTA, único consumidor: venta-directa.ts):
 *  - muestra código VT, prendas y total;
 *  - si viene de una reserva, muestra también su código RS y el cliente;
 *  - "Continuar al pago" y "Volver" emiten sus eventos hacia el padre --
 *    este componente nunca abre el modal de CU25 por sí mismo (ver
 *    procesar-pago.ts, el padre decide).
 */
describe('VentaResumen', () => {
  const ventaDirecta: VentaPresencialOut = {
    id: 1,
    codigo_venta: 'VT-00010',
    tipo: 'PRESENCIAL',
    estado: 'PENDIENTE_PAGO',
    origen: 'DIRECTA',
    total: 260,
    fecha_creacion: new Date().toISOString(),
    reserva: null,
    detalles: [
      {
        producto: { id: 5, nombre: 'Chompa Andina', imagen_principal_url: null },
        variante: { id: 9, talla: { id: 1, nombre: 'M' }, color: { id: 2, nombre: 'Negro' } },
        cantidad: 2,
        precio_unitario: 130,
        subtotal: 260,
      },
    ],
  };

  function crear(venta: VentaPresencialOut) {
    const fixture = TestBed.createComponent(VentaResumen);
    fixture.componentRef.setInput('venta', venta);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  it('muestra código, prendas y total', () => {
    const fixture = crear(ventaDirecta);
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('VT-00010');
    expect(texto).toContain('Chompa Andina');
    expect(texto).toContain('Negro');
    expect(texto).toContain('M');
    expect(texto).toContain('260.00');
    expect(texto).not.toContain('PENDIENTE_PAGO');
  });

  it('con reserva, muestra el código RS y el nombre del cliente', () => {
    const ventaDesdeReserva: VentaPresencialOut = {
      ...ventaDirecta,
      origen: 'RESERVA',
      reserva: { codigo_reserva: 'RS-00042', cliente_nombre: 'Gabriela' },
    };
    const fixture = crear(ventaDesdeReserva);
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('RS-00042');
    expect(texto).toContain('Gabriela');
  });

  it('"Continuar al pago" y "Volver" emiten sus eventos hacia el padre', () => {
    const fixture = crear(ventaDirecta);
    const botones = Array.from(raiz(fixture).querySelectorAll('button'));

    const continuarSpy = vi.fn();
    fixture.componentInstance.continuarPago.subscribe(continuarSpy);
    const continuar = botones.find((b) => b.textContent?.includes('Continuar al pago')) as HTMLButtonElement;
    expect(continuar.disabled).toBe(false);
    continuar.click();
    expect(continuarSpy).toHaveBeenCalled();

    const volverSpy = vi.fn();
    fixture.componentInstance.volver.subscribe(volverSpy);
    const volver = botones.find((b) => b.textContent?.trim() === 'Volver') as HTMLButtonElement;
    volver.click();
    expect(volverSpy).toHaveBeenCalled();
  });
});
