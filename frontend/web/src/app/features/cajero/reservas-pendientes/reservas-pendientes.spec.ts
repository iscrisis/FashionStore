import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { ReservaDetallePanel, ReservaPanel } from '../../encargado/reservas/reservas.model';
import { ReservasPendientes } from './reservas-pendientes';

/**
 * Pruebas de la integración mínima de CU20 con el rol Cajero -- "Reservas
 * pendientes de atención":
 *  - consulta GET /reservas/cajero/pendientes (la sucursal la resuelve
 *    siempre el backend desde el token, esta pantalla nunca la envía);
 *  - cabeceras agrupadas (código, cliente, fecha, horario) con sus prendas
 *    "para caja" anidadas -- una tarjeta por reserva, no por prenda;
 *  - CU24 agrega "+ Nueva venta" (arriba, navega a /cajero/ventas/nueva);
 *  - CU25 -- "Cargar venta" (por tarjeta, NUNCA toda la tarjeta clicable)
 *    YA NO navega: crea/reutiliza la Venta (CU24) y abre el modal
 *    <app-procesar-pago> sobre esta misma pantalla; al confirmar el pago,
 *    la lista se refresca (esa reserva ya pasó a ATENDIDA).
 */
describe('ReservasPendientes (Cajero)', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    localStorage.setItem('fashionstore_token', 'token-de-prueba');
    localStorage.setItem(
      'fashionstore_usuario',
      JSON.stringify({ id: 1, nombre: 'Daniel', correo: 'daniel@fashionstore.com', rol: 'CAJERO' }),
    );
    await TestBed.configureTestingModule({
      imports: [ReservasPendientes],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    localStorage.clear();
    http.verify();
  });

  function crear() {
    const fixture = TestBed.createComponent(ReservasPendientes);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function detalleDePrueba(overrides: Partial<ReservaDetallePanel> = {}): ReservaDetallePanel {
    return {
      id: 100,
      reserva_id: 1,
      producto: { id: 10, nombre: 'Chaqueta Denim', imagen_principal_url: '/api/v1/media/productos/x.jpg' },
      variante: { id: 20, talla: { id: 1, nombre: 'M' }, color: { id: 2, nombre: 'Blanco' } },
      cantidad: 1,
      estado: 'LISTA_PARA_CAJA',
      ...overrides,
    };
  }

  function reservaDePrueba(overrides: Partial<ReservaPanel> = {}): ReservaPanel {
    return {
      id: 1,
      codigo_reserva: 'RS-00001',
      cliente: { id: 30, nombre: 'Gabriela' },
      estado_general: 'LISTA_PARA_CAJA',
      fecha_reserva: '2026-09-18',
      hora_inicio: '16:00:00',
      hora_fin: '17:00:00',
      fecha_creacion: '2026-09-10T12:00:00Z',
      detalles: [detalleDePrueba()],
      ...overrides,
    };
  }

  it('consulta GET /reservas/cajero/pendientes y muestra código, producto, talla, color, cliente, fecha y horario', () => {
    const fixture = crear();
    const req = http.expectOne(`${environment.apiUrl}/reservas/cajero/pendientes`);
    expect(req.request.method).toBe('GET');
    req.flush([reservaDePrueba()]);
    fixture.detectChanges();

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Reservas pendientes de atención');
    expect(texto).toContain('RS-00001');
    expect(texto).toContain('Chaqueta Denim');
    expect(texto).toContain('Blanco');
    expect(texto).toContain('M');
    expect(texto).toContain('Gabriela');
    expect(texto).toContain('18/09/2026');
    expect(texto).toContain('16:00 - 17:00');
    expect(texto).toContain('Lista para caja');
  });

  it('una reserva con varias prendas para caja muestra una sola tarjeta con todas anidadas', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/cajero/pendientes`).flush([
      reservaDePrueba({
        detalles: [
          detalleDePrueba({ id: 100, producto: { id: 10, nombre: 'Chaqueta', imagen_principal_url: null } }),
          detalleDePrueba({ id: 101, producto: { id: 11, nombre: 'Pantalón', imagen_principal_url: null } }),
        ],
      }),
    ]);
    fixture.detectChanges();

    expect(raiz(fixture).querySelectorAll('.reserva-card').length).toBe(1);
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Chaqueta');
    expect(texto).toContain('Pantalón');
  });

  it('NO muestra ningún botón de cobrar, registrar pago ni generar comprobante (CU25, fuera de alcance)', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/cajero/pendientes`).flush([reservaDePrueba()]);
    fixture.detectChanges();

    const textos = [
      ...Array.from(raiz(fixture).querySelectorAll('button')),
      ...Array.from(raiz(fixture).querySelectorAll('a')),
    ].map((el) => el.textContent?.trim().toLowerCase() ?? '');
    for (const prohibido of ['cobrar', 'pago', 'comprobante']) {
      expect(textos.some((texto) => texto.includes(prohibido))).toBe(false);
    }
  });

  it('CU24 -- "+ Nueva venta" enlaza a /cajero/ventas/nueva', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/cajero/pendientes`).flush([]);
    fixture.detectChanges();

    const enlace = raiz(fixture).querySelector('.page-header__accion') as HTMLAnchorElement;
    expect(enlace).toBeTruthy();
    expect(enlace.getAttribute('href')).toBe('/cajero/ventas/nueva');
  });

  it('CU25 -- "Cargar venta" (botón propio, nunca toda la tarjeta) crea/reutiliza la Venta y abre el modal de pago', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/cajero/pendientes`).flush([reservaDePrueba({ id: 7 })]);
    fixture.detectChanges();

    const boton = raiz(fixture).querySelector('.reserva-card__cargar-venta') as HTMLButtonElement;
    expect(boton).toBeTruthy();
    expect(boton.textContent).toContain('Cargar venta');
    expect(boton.getAttribute('routerLink')).toBeNull();

    // La tarjeta en sí no debe tener su propio (click) -- solo el botón.
    const tarjeta = raiz(fixture).querySelector('.reserva-card') as HTMLElement;
    expect(tarjeta.getAttribute('routerLink')).toBeNull();

    expect(raiz(fixture).querySelector('app-procesar-pago')).toBeNull();
    boton.click();
    fixture.detectChanges();

    const req = http.expectOne(`${environment.apiUrl}/ventas-presenciales/desde-reserva/7`);
    expect(req.request.method).toBe('POST');
    req.flush({
      id: 3,
      codigo_venta: 'VT-00003',
      tipo: 'PRESENCIAL',
      estado: 'PENDIENTE_PAGO',
      origen: 'RESERVA',
      total: 90,
      fecha_creacion: new Date().toISOString(),
      reserva: { codigo_reserva: 'RS-00001', cliente_nombre: 'Gabriela' },
      detalles: [],
    });
    fixture.detectChanges();

    // NUNCA navega -- el modal aparece sobre esta misma pantalla.
    expect(raiz(fixture).querySelector('app-procesar-pago')).not.toBeNull();
    expect(raiz(fixture).textContent).toContain('VT-00003');
  });

  it('sin reservas, muestra el estado vacío limpio', () => {
    const fixture = crear();
    http.expectOne(`${environment.apiUrl}/reservas/cajero/pendientes`).flush([]);
    fixture.detectChanges();

    expect(raiz(fixture).textContent).toContain('No hay reservas pendientes de atención.');
    expect(raiz(fixture).querySelector('table')).toBeNull();
  });
});
