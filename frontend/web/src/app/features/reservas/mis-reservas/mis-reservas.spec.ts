import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { EstadoReserva, ReservaDetalleOut, ReservaOut } from '../crear-reserva/crear-reserva.model';
import { MisReservas } from './mis-reservas';

/**
 * Pruebas de CU18 -- Consultar reserva (Cliente): una tarjeta por RESERVA
 * (cabecera: código, sucursal+ciudad, fecha, horario, estado_general), con
 * sus prendas (`detalles`) anidadas -- nunca ids ni el enum crudo de
 * `estado`. Las reservas quedan separadas por tabs Pendientes/Atendidas/
 * Canceladas (por `estado_general`) -- Pendientes abre por defecto, sin una
 * pestaña "Todas".
 */
describe('MisReservas', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MisReservas],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  function crear() {
    const fixture = TestBed.createComponent(MisReservas);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function tab(fixture: ReturnType<typeof crear>, etiqueta: string): HTMLButtonElement {
    const boton = Array.from(raiz(fixture).querySelectorAll('.tab-reserva')).find(
      (el) => el.textContent?.trim() === etiqueta,
    ) as HTMLButtonElement;
    if (!boton) {
      throw new Error(`No se encontró la pestaña "${etiqueta}"`);
    }
    return boton;
  }

  function irATab(fixture: ReturnType<typeof crear>, etiqueta: string): void {
    tab(fixture, etiqueta).click();
    fixture.detectChanges();
  }

  function detalleDePrueba(overrides: Partial<ReservaDetalleOut> = {}): ReservaDetalleOut {
    return {
      id: 100,
      producto: { id: 10, nombre: 'Chaqueta Denim', imagen_principal_url: '/api/v1/media/productos/x.jpg' },
      variante: { id: 20, talla: { id: 1, nombre: 'M' }, color: { id: 2, nombre: 'Blanco' } },
      cantidad: 1,
      estado: 'PENDIENTE',
      ...overrides,
    };
  }

  function reservaDePrueba(overrides: Partial<ReservaOut> = {}): ReservaOut {
    const estado = (overrides.estado_general ?? 'PENDIENTE') as EstadoReserva;
    return {
      id: 1,
      codigo_reserva: 'RS-00001',
      sucursal: { id: 3, nombre: 'Mall Ventura', ciudad: { id: 4, nombre: 'Santa Cruz' } },
      estado_general: estado,
      fecha_reserva: '2026-09-18',
      hora_inicio: '16:00:00',
      hora_fin: '17:00:00',
      fecha_creacion: '2026-09-10T12:00:00Z',
      detalles: [detalleDePrueba({ id: (overrides.id ?? 1) * 100, estado })],
      ...overrides,
    };
  }

  it('abre por defecto en la pestaña Pendientes', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/mias`).flush([reservaDePrueba()]);
    fixture.detectChanges();

    expect(tab(fixture, 'Pendientes').classList.contains('is-active')).toBe(true);
    expect(tab(fixture, 'Atendidas').classList.contains('is-active')).toBe(false);
    expect(tab(fixture, 'Canceladas').classList.contains('is-active')).toBe(false);
    // No existe una pestaña "Todas".
    expect(raiz(fixture).querySelectorAll('.tab-reserva').length).toBe(3);
  });

  it('renderiza una tarjeta con código, sucursal, ciudad, fecha, horario, y el detalle con producto/color/talla/estado amigable', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/mias`).flush([reservaDePrueba()]);
    fixture.detectChanges();

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('RS-00001');
    expect(texto).toContain('Chaqueta Denim');
    expect(texto).toContain('Blanco');
    expect(texto).toContain('M');
    expect(texto).toContain('Mall Ventura');
    expect(texto).toContain('Santa Cruz');
    expect(texto).toContain('18/09/2026');
    expect(texto).toContain('16:00 - 17:00');
    expect(texto).toContain('Pendiente de preparación');
    // Nunca el enum crudo del backend, ni ids técnicos.
    expect(texto).not.toContain('PENDIENTE');
  });

  it('la imagen del producto se renderiza con la URL resuelta', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/mias`).flush([reservaDePrueba()]);
    fixture.detectChanges();

    const img = raiz(fixture).querySelector('.detalle-prenda__imagen img');
    expect(img).not.toBeNull();
  });

  it('sin reservas, cada pestaña muestra su propio estado vacío limpio y ninguna tabla', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/mias`).flush([]);
    fixture.detectChanges();

    expect(raiz(fixture).textContent).toContain('No tienes reservas pendientes.');
    expect(raiz(fixture).querySelector('table')).toBeNull();

    irATab(fixture, 'Atendidas');
    expect(raiz(fixture).textContent).toContain('No tienes reservas atendidas.');

    irATab(fixture, 'Canceladas');
    expect(raiz(fixture).textContent).toContain('No tienes reservas canceladas.');
  });

  it('cada estado aparece únicamente en su propia pestaña, nunca mezcladas', () => {
    const fixture = crear();
    http
      .expectOne(`${environment.apiUrl}/reservas/mias`)
      .flush([
        reservaDePrueba({
          id: 1,
          detalles: [detalleDePrueba({ id: 100, producto: { id: 10, nombre: 'Pendiente Prenda', imagen_principal_url: null } })],
        }),
        reservaDePrueba({
          id: 2,
          estado_general: 'ATENDIDA',
          detalles: [detalleDePrueba({ id: 200, estado: 'ATENDIDA', producto: { id: 11, nombre: 'Atendida Prenda', imagen_principal_url: null } })],
        }),
        reservaDePrueba({
          id: 3,
          estado_general: 'CANCELADA',
          detalles: [detalleDePrueba({ id: 300, estado: 'CANCELADA', producto: { id: 12, nombre: 'Cancelada Prenda', imagen_principal_url: null } })],
        }),
      ]);
    fixture.detectChanges();

    // Pendientes (por defecto): solo la PENDIENTE.
    let texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Pendiente Prenda');
    expect(texto).not.toContain('Atendida Prenda');
    expect(texto).not.toContain('Cancelada Prenda');

    irATab(fixture, 'Atendidas');
    texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Atendida Prenda');
    expect(texto).toContain('Atendida');
    expect(texto).not.toContain('Pendiente Prenda');
    expect(texto).not.toContain('Cancelada Prenda');

    irATab(fixture, 'Canceladas');
    texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Cancelada Prenda');
    expect(texto).toContain('Cancelada');
    expect(texto).not.toContain('Pendiente Prenda');
    expect(texto).not.toContain('Atendida Prenda');
  });

  it('el botón "Cancelar" solo aparece en la pestaña Pendientes', () => {
    const fixture = crear();
    http
      .expectOne(`${environment.apiUrl}/reservas/mias`)
      .flush([reservaDePrueba({ id: 1 }), reservaDePrueba({ id: 2, estado_general: 'ATENDIDA' })]);
    fixture.detectChanges();

    expect(raiz(fixture).querySelector('.cancelar-btn')).not.toBeNull();

    irATab(fixture, 'Atendidas');
    expect(raiz(fixture).querySelector('.cancelar-btn')).toBeNull();
  });

  it('PREPARADA/EN_ATENCION/LISTA_PARA_CAJA (CU20) aparecen junto a PENDIENTE en la pestaña Pendientes', () => {
    const fixture = crear();
    http
      .expectOne(`${environment.apiUrl}/reservas/mias`)
      .flush([
        reservaDePrueba({
          id: 1,
          estado_general: 'PREPARADA',
          detalles: [detalleDePrueba({ id: 100, estado: 'PREPARADA', producto: { id: 10, nombre: 'Preparada Prenda', imagen_principal_url: null } })],
        }),
        reservaDePrueba({
          id: 2,
          estado_general: 'EN_ATENCION',
          detalles: [detalleDePrueba({ id: 200, estado: 'EN_ATENCION', producto: { id: 11, nombre: 'Atencion Prenda', imagen_principal_url: null } })],
        }),
        reservaDePrueba({
          id: 3,
          estado_general: 'LISTA_PARA_CAJA',
          detalles: [detalleDePrueba({ id: 300, estado: 'LISTA_PARA_CAJA', producto: { id: 12, nombre: 'Caja Prenda', imagen_principal_url: null } })],
        }),
      ]);
    fixture.detectChanges();

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Preparada Prenda');
    expect(texto).toContain('Lista para tu visita');
    expect(texto).toContain('Atencion Prenda');
    expect(texto).toContain('En atención');
    expect(texto).toContain('Caja Prenda');
    expect(texto).toContain('En proceso en sucursal');
  });

  it('solo detalles PENDIENTE y PREPARADA muestran el botón de cancelar dentro de la pestaña Pendientes', () => {
    const fixture = crear();
    http
      .expectOne(`${environment.apiUrl}/reservas/mias`)
      .flush([
        reservaDePrueba({ id: 1, estado_general: 'PENDIENTE' }),
        reservaDePrueba({ id: 2, estado_general: 'PREPARADA', detalles: [detalleDePrueba({ id: 200, estado: 'PREPARADA' })] }),
        reservaDePrueba({ id: 3, estado_general: 'EN_ATENCION', detalles: [detalleDePrueba({ id: 300, estado: 'EN_ATENCION' })] }),
        reservaDePrueba({ id: 4, estado_general: 'LISTA_PARA_CAJA', detalles: [detalleDePrueba({ id: 400, estado: 'LISTA_PARA_CAJA' })] }),
      ]);
    fixture.detectChanges();

    // 2 botones (PENDIENTE + PREPARADA), no 4 -- EN_ATENCION y
    // LISTA_PARA_CAJA ya están en manos del Encargado (CU20).
    expect(raiz(fixture).querySelectorAll('.cancelar-btn').length).toBe(2);
  });

  it('VENCIDA se agrupa junto a CANCELADA, con su propio texto distintivo', () => {
    const fixture = crear();
    http
      .expectOne(`${environment.apiUrl}/reservas/mias`)
      .flush([
        reservaDePrueba({
          id: 1,
          estado_general: 'VENCIDA',
          detalles: [detalleDePrueba({ id: 100, estado: 'VENCIDA', producto: { id: 10, nombre: 'Vencida Prenda', imagen_principal_url: null } })],
        }),
      ]);
    fixture.detectChanges();

    irATab(fixture, 'Canceladas');
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Vencida Prenda');
    expect(texto).toContain('Vencida');
    expect(texto).not.toContain('No tienes reservas canceladas.');
  });

  it('una reserva con varias prendas muestra una sola tarjeta con todas anidadas', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/mias`).flush([
      reservaDePrueba({
        id: 1,
        detalles: [
          detalleDePrueba({ id: 100, producto: { id: 10, nombre: 'Chaqueta', imagen_principal_url: null } }),
          detalleDePrueba({ id: 101, producto: { id: 11, nombre: 'Camisa', imagen_principal_url: null }, estado: 'CANCELADA' }),
        ],
      }),
    ]);
    fixture.detectChanges();

    expect(raiz(fixture).querySelectorAll('.reserva-card').length).toBe(1);
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Chaqueta');
    expect(texto).toContain('Camisa');
  });
});
