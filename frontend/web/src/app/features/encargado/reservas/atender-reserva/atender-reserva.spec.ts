import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../../environments/environment';
import { EstadoReservaPanel, ReservaDetallePanel } from '../reservas.model';
import { AtenderReserva } from './atender-reserva';

/**
 * Pruebas de CU20 -- Atender reserva de prendas (Encargado), acciones a
 * nivel DETALLE (una prenda dentro de una reserva). "Confirmar llegada" y
 * "Finalizar atención" NO viven aquí -- son acciones de la RESERVA completa
 * (ver reservas.spec.ts).
 *  - PENDIENTE muestra únicamente "Preparar prenda";
 *  - PREPARADA con la reserva EN_ATENCION muestra "No la compra"/"Enviar a
 *    caja"; PREPARADA sin la reserva en atención no muestra ningún botón
 *    (hay que confirmar la llegada primero, a nivel reserva);
 *  - ninguna decisión abre un modal de confirmación (no libera/toca stock
 *    de inmediato -- eso ocurre recién al "Finalizar atención" de toda la
 *    reserva, ver reservas.ts) -- se ejecutan directo;
 *  - cada acción llama al PATCH correspondiente y emite el detalle
 *    actualizado para que el panel reemplace esa prenda.
 */
describe('AtenderReserva', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AtenderReserva],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  function detalleDePrueba(overrides: Partial<ReservaDetallePanel> = {}): ReservaDetallePanel {
    return {
      id: 7,
      reserva_id: 1,
      producto: { id: 10, nombre: 'Chaqueta Denim', imagen_principal_url: null },
      variante: { id: 20, talla: { id: 1, nombre: 'M' }, color: { id: 2, nombre: 'Blanco' } },
      cantidad: 1,
      estado: 'PENDIENTE',
      ...overrides,
    };
  }

  function crear(detalle: ReservaDetallePanel, estadoGeneralReserva: EstadoReservaPanel = 'PENDIENTE') {
    const fixture = TestBed.createComponent(AtenderReserva);
    fixture.componentRef.setInput('detalle', detalle);
    fixture.componentRef.setInput('estadoGeneralReserva', estadoGeneralReserva);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function botonesTexto(fixture: ReturnType<typeof crear>): string[] {
    return Array.from(raiz(fixture).querySelectorAll('.atender-acciones button')).map(
      (b) => b.textContent?.trim() ?? '',
    );
  }

  it('PENDIENTE muestra únicamente "Preparar prenda"', () => {
    const fixture = crear(detalleDePrueba({ estado: 'PENDIENTE' }), 'PENDIENTE');
    expect(botonesTexto(fixture)).toEqual(['Preparar prenda']);
  });

  it('PREPARADA con la reserva EN_ATENCION muestra "No la compra" y "Enviar a caja"', () => {
    const fixture = crear(detalleDePrueba({ estado: 'PREPARADA' }), 'EN_ATENCION');
    expect(botonesTexto(fixture)).toEqual(['No la compra', 'Enviar a caja']);
  });

  it('PREPARADA sin la reserva todavía en atención no muestra ningún botón', () => {
    const fixture = crear(detalleDePrueba({ estado: 'PREPARADA' }), 'PENDIENTE');
    expect(raiz(fixture).querySelector('.atender-acciones')).toBeNull();
  });

  it('LISTA_PARA_CAJA, ATENDIDA, CANCELADA y VENCIDA no muestran ningún botón', () => {
    for (const estado of ['LISTA_PARA_CAJA', 'ATENDIDA', 'CANCELADA', 'VENCIDA'] as const) {
      const fixture = crear(detalleDePrueba({ estado }), 'EN_ATENCION');
      expect(raiz(fixture).querySelector('.atender-acciones')).toBeNull();
    }
  });

  it('"Preparar prenda" llama de inmediato al backend', () => {
    const fixture = crear(detalleDePrueba({ estado: 'PENDIENTE' }), 'PENDIENTE');
    (raiz(fixture).querySelector('.atender-acciones button') as HTMLButtonElement).click();

    const req = http.expectOne(`${environment.apiUrl}/reservas/detalles/7/preparar`);
    expect(req.request.method).toBe('PATCH');
    req.flush(detalleDePrueba({ estado: 'PREPARADA' }));
    fixture.detectChanges();
  });

  it('"No la compra" llama de inmediato al backend, sin modal, y emite el detalle actualizado', () => {
    const fixture = crear(detalleDePrueba({ estado: 'PREPARADA' }), 'EN_ATENCION');
    let emitida: ReservaDetallePanel | undefined;
    fixture.componentInstance.actualizada.subscribe((r) => (emitida = r));

    const botones = raiz(fixture).querySelectorAll('.atender-acciones button');
    (botones[0] as HTMLButtonElement).click();

    const req = http.expectOne(`${environment.apiUrl}/reservas/detalles/7/no-la-compra`);
    expect(req.request.method).toBe('PATCH');
    req.flush(detalleDePrueba({ estado: 'ATENDIDA' }));
    fixture.detectChanges();

    expect(emitida?.estado).toBe('ATENDIDA');
  });

  it('"Enviar a caja" llama de inmediato al backend, sin modal, y emite el detalle actualizado', () => {
    const fixture = crear(detalleDePrueba({ estado: 'PREPARADA' }), 'EN_ATENCION');
    let emitida: ReservaDetallePanel | undefined;
    fixture.componentInstance.actualizada.subscribe((r) => (emitida = r));

    const botones = raiz(fixture).querySelectorAll('.atender-acciones button');
    (botones[1] as HTMLButtonElement).click();

    const req = http.expectOne(`${environment.apiUrl}/reservas/detalles/7/enviar-a-caja`);
    expect(req.request.method).toBe('PATCH');
    req.flush(detalleDePrueba({ estado: 'LISTA_PARA_CAJA' }));
    fixture.detectChanges();

    expect(emitida?.estado).toBe('LISTA_PARA_CAJA');
  });

  it('nunca llama a confirmar-llegada ni a finalizar-atencion -- son acciones de la reserva, no de la prenda', () => {
    const fixture = crear(detalleDePrueba({ estado: 'PREPARADA' }), 'EN_ATENCION');
    const botones = raiz(fixture).querySelectorAll('.atender-acciones button');
    (botones[1] as HTMLButtonElement).click();

    http.expectOne(`${environment.apiUrl}/reservas/detalles/7/enviar-a-caja`).flush(
      detalleDePrueba({ estado: 'LISTA_PARA_CAJA' }),
    );
    http.expectNone(`${environment.apiUrl}/reservas/1/confirmar-llegada`);
    http.expectNone(`${environment.apiUrl}/reservas/1/finalizar-atencion`);
  });
});
