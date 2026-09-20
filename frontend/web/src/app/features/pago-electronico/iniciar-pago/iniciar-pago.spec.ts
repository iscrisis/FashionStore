import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { IniciarPago } from './iniciar-pago';

/**
 * Prueba de regresión para CU23 -- "Iniciar pago" ('/pago/iniciar'):
 *  - con un venta_id válido, pide POST /pagos/checkout y redirige el
 *    navegador (misma pestaña, `window.location.href`) a la URL que
 *    devuelve el backend -- nunca abre una pestaña/popup nueva;
 *  - si el backend rechaza (p. ej. ya no hay disponibilidad), muestra un
 *    estado amigable con "Reintentar pago";
 *  - sin venta_id en la URL, no llama al backend y muestra el error.
 */
describe('IniciarPago', () => {
  let httpMock: HttpTestingController;
  let hrefAsignado: string | null;

  beforeEach(() => {
    hrefAsignado = null;
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        ...window.location,
        set href(valor: string) {
          hrefAsignado = valor;
        },
      },
    });
  });

  function crear(ventaId: string | null) {
    const paramMap = new Map(ventaId ? [['venta_id', ventaId]] : []);
    return TestBed.configureTestingModule({
      imports: [IniciarPago],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: paramMap } } },
      ],
    })
      .compileComponents()
      .then(() => {
        httpMock = TestBed.inject(HttpTestingController);
        const fixture = TestBed.createComponent(IniciarPago);
        fixture.detectChanges();
        return fixture;
      });
  }

  function raiz(fixture: Awaited<ReturnType<typeof crear>>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    httpMock.verify();
  });

  it('con venta_id válido, llama a POST /pagos/checkout y redirige a la URL de Stripe (misma pestaña)', async () => {
    const fixture = await crear('42');

    const req = httpMock.expectOne(`${environment.apiUrl}/pagos/checkout`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ venta_id: 42 });

    req.flush({ checkout_url: 'https://checkout.stripe.com/test/session_abc' });
    fixture.detectChanges();

    expect(hrefAsignado).toBe('https://checkout.stripe.com/test/session_abc');
  });

  it('si el backend rechaza, muestra el mensaje amigable con "Reintentar pago"', async () => {
    const fixture = await crear('42');

    const req = httpMock.expectOne(`${environment.apiUrl}/pagos/checkout`);
    req.flush(
      { detail: 'Ya no hay disponibilidad suficiente para completar esta compra.' },
      { status: 422, statusText: 'Unprocessable Entity' },
    );
    fixture.detectChanges();

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Ya no hay disponibilidad suficiente para completar esta compra.');
    expect(raiz(fixture).querySelector('button')?.textContent).toContain('Reintentar pago');
    expect(hrefAsignado).toBeNull();
  });

  it('sin venta_id, no llama al backend y muestra el error', async () => {
    const fixture = await crear(null);

    httpMock.expectNone(`${environment.apiUrl}/pagos/checkout`);
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('No se encontró la compra a pagar.');
  });
});
