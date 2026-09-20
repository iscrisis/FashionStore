import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { EstadoReservaPanel, ReservaDetallePanel, ReservaPanel } from './reservas.model';
import { Reservas } from './reservas';

/**
 * Pruebas de CU20 -- panel "Reservas" del Encargado: agrupa en Pendientes /
 * En atención / Finalizadas (nunca mezcladas) por `estado_general` de la
 * reserva, cada grupo tiene su propio estado vacío, y cada tarjeta muestra
 * la cabecera (código, cliente, fecha, horario) con sus prendas anidadas.
 *
 * Dos niveles de acción, nunca mezclados:
 *  - "Confirmar llegada" -- UN botón por reserva (nunca repetido por
 *    prenda), visible solo si estado_general es PENDIENTE/PREPARADA.
 *  - "Finalizar atención" -- UN botón por reserva, visible solo
 *    EN_ATENCION, deshabilitado mientras algún detalle siga sin decisión,
 *    detrás de un modal con el resumen de "para caja"/"no comprará".
 */
describe('Reservas (panel del Encargado)', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Reservas],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  function crear() {
    const fixture = TestBed.createComponent(Reservas);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function grupo(fixture: ReturnType<typeof crear>, etiqueta: string): HTMLButtonElement {
    const boton = Array.from(raiz(fixture).querySelectorAll('.grupo-reserva')).find(
      (el) => el.textContent?.trim() === etiqueta,
    ) as HTMLButtonElement;
    if (!boton) {
      throw new Error(`No se encontró el grupo "${etiqueta}"`);
    }
    return boton;
  }

  function irAGrupo(fixture: ReturnType<typeof crear>, etiqueta: string): void {
    grupo(fixture, etiqueta).click();
    fixture.detectChanges();
  }

  function detalleDePrueba(overrides: Partial<ReservaDetallePanel> = {}): ReservaDetallePanel {
    return {
      id: 100,
      reserva_id: 1,
      producto: { id: 10, nombre: 'Chaqueta Denim', imagen_principal_url: null },
      variante: { id: 20, talla: { id: 1, nombre: 'M' }, color: { id: 2, nombre: 'Blanco' } },
      cantidad: 1,
      estado: 'PENDIENTE',
      ...overrides,
    };
  }

  function reservaDePrueba(overrides: Partial<ReservaPanel> = {}): ReservaPanel {
    const estado = (overrides.estado_general ?? 'PENDIENTE') as EstadoReservaPanel;
    return {
      id: 1,
      codigo_reserva: 'RS-00001',
      cliente: { id: 30, nombre: 'Gabriela' },
      estado_general: estado,
      fecha_reserva: '2026-09-18',
      hora_inicio: '16:00:00',
      hora_fin: '17:00:00',
      fecha_creacion: '2026-09-10T12:00:00Z',
      detalles: [detalleDePrueba({ reserva_id: overrides.id ?? 1, estado })],
      ...overrides,
    };
  }

  function botonConfirmarLlegada(fixture: ReturnType<typeof crear>): HTMLButtonElement | null {
    return raiz(fixture).querySelector('.reserva-card__confirmar-llegada');
  }

  function botonFinalizar(fixture: ReturnType<typeof crear>): HTMLButtonElement | null {
    return raiz(fixture).querySelector('.reserva-card__finalizar');
  }

  it('abre por defecto en el grupo Pendientes', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([reservaDePrueba()]);
    fixture.detectChanges();

    expect(grupo(fixture, 'Pendientes').classList.contains('is-active')).toBe(true);
    expect(grupo(fixture, 'En atención').classList.contains('is-active')).toBe(false);
    expect(grupo(fixture, 'Finalizadas').classList.contains('is-active')).toBe(false);
  });

  it('renderiza la tarjeta con código, cliente, fecha, horario y el detalle con producto/color/talla/estado', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([reservaDePrueba()]);
    fixture.detectChanges();

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('RS-00001');
    expect(texto).toContain('Chaqueta Denim');
    expect(texto).toContain('Blanco');
    expect(texto).toContain('M');
    expect(texto).toContain('Gabriela');
    expect(texto).toContain('18/09/2026');
    expect(texto).toContain('16:00 - 17:00');
    expect(texto).toContain('Pendiente');
  });

  it('cada grupo muestra su propio estado vacío', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([]);
    fixture.detectChanges();

    expect(raiz(fixture).textContent).toContain('No hay reservas pendientes.');

    irAGrupo(fixture, 'En atención');
    expect(raiz(fixture).textContent).toContain('No hay reservas en atención.');

    irAGrupo(fixture, 'Finalizadas');
    expect(raiz(fixture).textContent).toContain('No hay reservas finalizadas.');
  });

  it('PENDIENTE y PREPARADA se agrupan en Pendientes; EN_ATENCION en su propio grupo; el resto en Finalizadas', () => {
    const fixture = crear();
    http
      .expectOne(`${environment.apiUrl}/reservas/panel`)
      .flush([
        reservaDePrueba({
          id: 1,
          estado_general: 'PENDIENTE',
          detalles: [detalleDePrueba({ reserva_id: 1, producto: { id: 10, nombre: 'Pendiente Prenda', imagen_principal_url: null } })],
        }),
        reservaDePrueba({
          id: 2,
          estado_general: 'PREPARADA',
          detalles: [detalleDePrueba({ reserva_id: 2, estado: 'PREPARADA', producto: { id: 11, nombre: 'Preparada Prenda', imagen_principal_url: null } })],
        }),
        reservaDePrueba({
          id: 3,
          estado_general: 'EN_ATENCION',
          detalles: [detalleDePrueba({ reserva_id: 3, estado: 'PREPARADA', producto: { id: 12, nombre: 'Atencion Prenda', imagen_principal_url: null } })],
        }),
        reservaDePrueba({
          id: 4,
          estado_general: 'ATENDIDA',
          detalles: [detalleDePrueba({ reserva_id: 4, estado: 'ATENDIDA', producto: { id: 13, nombre: 'Atendida Prenda', imagen_principal_url: null } })],
        }),
        reservaDePrueba({
          id: 5,
          estado_general: 'LISTA_PARA_CAJA',
          detalles: [detalleDePrueba({ reserva_id: 5, estado: 'LISTA_PARA_CAJA', producto: { id: 14, nombre: 'Caja Prenda', imagen_principal_url: null } })],
        }),
        reservaDePrueba({
          id: 6,
          estado_general: 'CANCELADA',
          detalles: [detalleDePrueba({ reserva_id: 6, estado: 'CANCELADA', producto: { id: 15, nombre: 'Cancelada Prenda', imagen_principal_url: null } })],
        }),
        reservaDePrueba({
          id: 7,
          estado_general: 'VENCIDA',
          detalles: [detalleDePrueba({ reserva_id: 7, estado: 'VENCIDA', producto: { id: 16, nombre: 'Vencida Prenda', imagen_principal_url: null } })],
        }),
      ]);
    fixture.detectChanges();

    let texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Pendiente Prenda');
    expect(texto).toContain('Preparada Prenda');
    expect(texto).not.toContain('Atencion Prenda');
    expect(texto).not.toContain('Atendida Prenda');

    irAGrupo(fixture, 'En atención');
    texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Atencion Prenda');
    expect(texto).not.toContain('Pendiente Prenda');
    expect(texto).not.toContain('Atendida Prenda');

    irAGrupo(fixture, 'Finalizadas');
    texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Atendida Prenda');
    expect(texto).toContain('Caja Prenda');
    expect(texto).toContain('Cancelada Prenda');
    expect(texto).toContain('Vencida Prenda');
    expect(texto).not.toContain('Pendiente Prenda');
    expect(texto).not.toContain('Atencion Prenda');
  });

  it('sin reservas del todo, no se muestra ninguna tabla técnica', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([]);
    fixture.detectChanges();

    expect(raiz(fixture).querySelector('table')).toBeNull();
  });

  it('una reserva con varias prendas muestra todas anidadas en la misma tarjeta', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([
      reservaDePrueba({
        id: 1,
        detalles: [
          detalleDePrueba({ id: 100, reserva_id: 1, producto: { id: 10, nombre: 'Chaqueta', imagen_principal_url: null } }),
          detalleDePrueba({ id: 101, reserva_id: 1, producto: { id: 11, nombre: 'Camisa', imagen_principal_url: null }, estado: 'CANCELADA' }),
        ],
      }),
    ]);
    fixture.detectChanges();

    const tarjetas = raiz(fixture).querySelectorAll('.reserva-card');
    expect(tarjetas.length).toBe(1);
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Chaqueta');
    expect(texto).toContain('Camisa');
  });

  // --------------------------------------------------------------------
  // "Confirmar llegada" -- un solo botón por reserva.
  // --------------------------------------------------------------------

  it('"Confirmar llegada" aparece una sola vez, solo si estado_general es PENDIENTE/PREPARADA', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([
      reservaDePrueba({ id: 1, estado_general: 'PREPARADA', detalles: [detalleDePrueba({ reserva_id: 1, estado: 'PREPARADA' })] }),
    ]);
    fixture.detectChanges();

    const botones = raiz(fixture).querySelectorAll('.reserva-card__confirmar-llegada');
    expect(botones.length).toBe(1);
  });

  it('"Confirmar llegada" no aparece si la reserva ya está EN_ATENCION o finalizada', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([
      reservaDePrueba({ id: 1, estado_general: 'EN_ATENCION', detalles: [detalleDePrueba({ reserva_id: 1, estado: 'PREPARADA' })] }),
    ]);
    fixture.detectChanges();
    irAGrupo(fixture, 'En atención');

    expect(botonConfirmarLlegada(fixture)).toBeNull();
  });

  it('confirmar llegada llama a PATCH /reservas/:id/confirmar-llegada y actualiza la cabecera sin tocar los detalles', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([
      reservaDePrueba({ id: 1, estado_general: 'PREPARADA', detalles: [detalleDePrueba({ id: 100, reserva_id: 1, estado: 'PREPARADA' })] }),
    ]);
    fixture.detectChanges();

    botonConfirmarLlegada(fixture)!.click();

    const req = http.expectOne(`${environment.apiUrl}/reservas/1/confirmar-llegada`);
    expect(req.request.method).toBe('PATCH');
    req.flush(
      reservaDePrueba({
        id: 1,
        estado_general: 'EN_ATENCION',
        detalles: [detalleDePrueba({ id: 100, reserva_id: 1, estado: 'PREPARADA' })],
      }),
    );
    fixture.detectChanges();

    irAGrupo(fixture, 'En atención');
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('En atención');
    expect(texto).toContain('Preparada'); // el detalle conserva su propio estado.
  });

  // --------------------------------------------------------------------
  // "Finalizar atención" -- deshabilitado con decisiones pendientes.
  // --------------------------------------------------------------------

  it('"Finalizar atención" solo aparece EN_ATENCION, y deshabilitado si hay un detalle sin decisión', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([
      reservaDePrueba({
        id: 1,
        estado_general: 'EN_ATENCION',
        detalles: [
          detalleDePrueba({ id: 100, reserva_id: 1, estado: 'LISTA_PARA_CAJA' }),
          detalleDePrueba({ id: 101, reserva_id: 1, estado: 'PREPARADA' }),
        ],
      }),
    ]);
    fixture.detectChanges();
    irAGrupo(fixture, 'En atención');

    const boton = botonFinalizar(fixture);
    expect(boton).not.toBeNull();
    expect(boton!.disabled).toBe(true);
  });

  it('"Finalizar atención" se habilita cuando todos los detalles ya tienen una decisión', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([
      reservaDePrueba({
        id: 1,
        estado_general: 'EN_ATENCION',
        detalles: [
          detalleDePrueba({ id: 100, reserva_id: 1, estado: 'LISTA_PARA_CAJA' }),
          detalleDePrueba({ id: 101, reserva_id: 1, estado: 'ATENDIDA' }),
        ],
      }),
    ]);
    fixture.detectChanges();
    irAGrupo(fixture, 'En atención');

    expect(botonFinalizar(fixture)!.disabled).toBe(false);
  });

  it('finalizar atención abre un modal con el resumen para caja / no comprará', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([
      reservaDePrueba({
        id: 1,
        estado_general: 'EN_ATENCION',
        detalles: [
          detalleDePrueba({ id: 100, reserva_id: 1, estado: 'LISTA_PARA_CAJA', producto: { id: 10, nombre: 'Chaqueta', imagen_principal_url: null } }),
          detalleDePrueba({ id: 101, reserva_id: 1, estado: 'ATENDIDA', producto: { id: 11, nombre: 'Camisa', imagen_principal_url: null } }),
        ],
      }),
    ]);
    fixture.detectChanges();
    irAGrupo(fixture, 'En atención');

    botonFinalizar(fixture)!.click();
    fixture.detectChanges();

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('¿Finalizar la atención de esta reserva?');
    expect(texto).toContain('Para caja');
    expect(texto).toContain('Chaqueta');
    expect(texto).toContain('No comprará');
    expect(texto).toContain('Camisa');
    http.expectNone(`${environment.apiUrl}/reservas/1/finalizar-atencion`);
  });

  it('"Volver" cierra el modal sin llamar al backend', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([
      reservaDePrueba({
        id: 1,
        estado_general: 'EN_ATENCION',
        detalles: [detalleDePrueba({ id: 100, reserva_id: 1, estado: 'ATENDIDA' })],
      }),
    ]);
    fixture.detectChanges();
    irAGrupo(fixture, 'En atención');

    botonFinalizar(fixture)!.click();
    fixture.detectChanges();
    (raiz(fixture).querySelector('.reserva-modal__volver') as HTMLButtonElement).click();
    fixture.detectChanges();

    expect(raiz(fixture).querySelector('.reserva-modal-overlay')).toBeNull();
    http.expectNone(`${environment.apiUrl}/reservas/1/finalizar-atencion`);
  });

  it('confirmar en el modal llama a PATCH finalizar-atencion y actualiza la cabecera', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/panel`).flush([
      reservaDePrueba({
        id: 1,
        estado_general: 'EN_ATENCION',
        detalles: [detalleDePrueba({ id: 100, reserva_id: 1, estado: 'LISTA_PARA_CAJA' })],
      }),
    ]);
    fixture.detectChanges();
    irAGrupo(fixture, 'En atención');

    botonFinalizar(fixture)!.click();
    fixture.detectChanges();
    (raiz(fixture).querySelector('.reserva-modal__confirmar') as HTMLButtonElement).click();

    const req = http.expectOne(`${environment.apiUrl}/reservas/1/finalizar-atencion`);
    expect(req.request.method).toBe('PATCH');
    req.flush(
      reservaDePrueba({
        id: 1,
        estado_general: 'LISTA_PARA_CAJA',
        detalles: [detalleDePrueba({ id: 100, reserva_id: 1, estado: 'LISTA_PARA_CAJA' })],
      }),
    );
    fixture.detectChanges();

    expect(raiz(fixture).querySelector('.reserva-modal-overlay')).toBeNull();
    irAGrupo(fixture, 'Finalizadas');
    expect(raiz(fixture).textContent).toContain('RS-00001');
  });
});
