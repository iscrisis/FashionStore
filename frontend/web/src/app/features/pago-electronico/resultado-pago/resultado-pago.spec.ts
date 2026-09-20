import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { VentaPagadaOut } from '../pago-electronico.model';
import { ResultadoPago } from './resultado-pago';

/**
 * Prueba de regresión para CU23 -- "Resultado de pago" ('/pago/resultado'):
 *  - con `session_id` en la URL, llama a POST /pagos/verificar y SOLO si
 *    responde 200 muestra "COMPRA REALIZADA" (código VT, "Pago realizado
 *    correctamente", total, sucursal+ciudad) -- Angular nunca decide esto
 *    por sí solo;
 *  - si el backend responde que el pago no se completó (o directamente
 *    llega `?cancelado=1` desde cancel_url), muestra "El pago no fue
 *    completado." con REINTENTAR PAGO y VOLVER -- nunca el detalle técnico
 *    ni "PENDIENTE_PAGO";
 *  - tras un pago exitoso, la pantalla NUNCA debe volver a decir
 *    "PENDIENTE_PAGO".
 */
describe('ResultadoPago', () => {
  let httpMock: HttpTestingController;

  const ventaPagada: VentaPagadaOut = {
    id: 42,
    codigo_venta: 'VT-00001',
    estado: 'PAGADA',
    total: 300,
    sucursal: { id: 1, nombre: 'Sucursal Centro', direccion: 'Av. Uno', ciudad: 'La Paz' },
  };

  function crear(params: Record<string, string>) {
    const paramMap = new Map(Object.entries(params));
    return TestBed.configureTestingModule({
      imports: [ResultadoPago],
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
        const fixture = TestBed.createComponent(ResultadoPago);
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

  it('con session_id válido y backend confirmando el pago, muestra COMPRA REALIZADA con código, total y retiro', async () => {
    const fixture = await crear({ session_id: 'cs_test_abc', venta_id: '42' });

    const req = httpMock.expectOne(`${environment.apiUrl}/pagos/verificar`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ session_id: 'cs_test_abc' });
    req.flush(ventaPagada);
    fixture.detectChanges();

    // CU31 -- apenas se confirma el pago, dispara en segundo plano el envío
    // del comprobante por correo (fire-and-forget, ver resultado-pago.ts).
    const reqComprobante = httpMock.expectOne(`${environment.apiUrl}/comprobantes/42/enviar`);
    expect(reqComprobante.request.method).toBe('POST');
    reqComprobante.flush({ enviado: true, mensaje: 'Comprobante enviado correctamente.' });

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Compra realizada');
    expect(texto).toContain('VT-00001');
    expect(texto).toContain('Pago realizado correctamente');
    expect(texto).toContain('300.00');
    expect(texto).toContain('Sucursal Centro');
    expect(texto).toContain('La Paz');
    expect(texto).toContain('Enviamos el comprobante a tu correo registrado.');
    expect(texto).not.toContain('PENDIENTE_PAGO');

    const enlaces = Array.from(raiz(fixture).querySelectorAll('a.btn')) as HTMLAnchorElement[];
    expect(enlaces.some((a) => a.textContent?.includes('Seguir comprando'))).toBe(true);
    const enlaceComprobante = enlaces.find((a) => a.textContent?.includes('Ver comprobante'));
    expect(enlaceComprobante?.getAttribute('href')).toBe('/comprobante/42');
  });

  it('si el backend dice que el pago no se completó, muestra el mensaje amigable con reintentar/volver', async () => {
    const fixture = await crear({ session_id: 'cs_test_abc', venta_id: '42' });

    const req = httpMock.expectOne(`${environment.apiUrl}/pagos/verificar`);
    req.flush({ detail: 'El pago no fue completado.' }, { status: 422, statusText: 'Unprocessable Entity' });
    fixture.detectChanges();

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('El pago no fue completado.');
    expect(texto).not.toContain('PENDIENTE_PAGO');
    const enlaces = Array.from(raiz(fixture).querySelectorAll('a.btn')) as HTMLAnchorElement[];
    expect(enlaces.some((a) => a.textContent?.includes('Reintentar pago'))).toBe(true);
    expect(enlaces.some((a) => a.getAttribute('href') === '/carrito')).toBe(true);
  });

  it('con ?cancelado=1 (cancel_url de Stripe), muestra el mensaje amigable SIN llamar al backend', async () => {
    const fixture = await crear({ cancelado: '1', venta_id: '42' });

    httpMock.expectNone(`${environment.apiUrl}/pagos/verificar`);
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('El pago no fue completado.');
  });
});
