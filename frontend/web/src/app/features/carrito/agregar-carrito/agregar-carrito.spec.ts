import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { environment } from '../../../../environments/environment';
import { AgregarCarrito } from './agregar-carrito';

/**
 * Prueba de regresión para CU21 -- "Agregar al carrito" desde producto-detalle:
 *  - sin sesión, el clic NUNCA llama al backend, solo redirige a /login con
 *    el returnUrl + "&agregarCarrito=1" (misma idea que CrearReserva, CU17,
 *    pero sin abrir ningún modal -- ver crear-reserva.spec.ts);
 *  - con sesión, el clic sí llama a POST /carrito/items exactamente UNA vez
 *    (protege contra doble clic mientras `submitting` está en true);
 *  - `autoAgregarParam` en true dispara el agregado solo (sin clic) una
 *    única vez y limpia el query param de la URL para que un F5 no repita
 *    el POST (ver _limpiarFlagUrl en agregar-carrito.ts).
 */
describe('AgregarCarrito', () => {
  let httpMock: HttpTestingController;

  function iniciarSesionComoCliente(): void {
    localStorage.setItem('fashionstore_token', 'token-de-prueba');
    localStorage.setItem(
      'fashionstore_usuario',
      JSON.stringify({ id: 1, nombre: 'Gabriela', correo: 'gabriela@fashionstore.com', rol: 'CLIENTE' }),
    );
  }

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [AgregarCarrito],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: new Map() } } },
      ],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  function crear(inputs: { productoVarianteId?: number | null; returnUrl?: string; autoAgregarParam?: boolean }) {
    const fixture = TestBed.createComponent(AgregarCarrito);
    fixture.componentRef.setInput('productoVarianteId', inputs.productoVarianteId ?? null);
    fixture.componentRef.setInput('returnUrl', inputs.returnUrl ?? '/producto/78?tallaId=1&colorId=2');
    fixture.componentRef.setInput('autoAgregarParam', inputs.autoAgregarParam ?? false);
    fixture.detectChanges();
    return fixture;
  }

  function boton(fixture: ReturnType<typeof crear>): HTMLButtonElement {
    return (fixture.nativeElement as HTMLElement).querySelector('button.agregar-carrito-btn')!;
  }

  it('sin variante seleccionada, el botón queda deshabilitado', () => {
    const fixture = crear({ productoVarianteId: null });
    expect(boton(fixture).disabled).toBe(true);
  });

  it('sin sesión, el clic redirige a /login con returnUrl + agregarCarrito=1 y no llama al backend', () => {
    const fixture = crear({ productoVarianteId: 208, returnUrl: '/producto/78?tallaId=1&colorId=2' });
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    boton(fixture).click();
    fixture.detectChanges();

    expect(navigateSpy).toHaveBeenCalledWith(['/login'], {
      queryParams: { returnUrl: '/producto/78?tallaId=1&colorId=2&agregarCarrito=1' },
    });
    httpMock.expectNone(`${environment.apiUrl}/carrito/items`);
  });

  it('con sesión, el clic llama a POST /carrito/items una sola vez', () => {
    iniciarSesionComoCliente();
    const fixture = crear({ productoVarianteId: 208 });

    boton(fixture).click();
    fixture.detectChanges();

    const req = httpMock.expectOne(`${environment.apiUrl}/carrito/items`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ producto_variante_id: 208 });
    req.flush({ items: [], subtotal_seleccionado: 0, fecha_actualizacion: new Date().toISOString() });
  });

  it('autoAgregarParam con sesión dispara el agregado una sola vez, sin clic', () => {
    iniciarSesionComoCliente();
    const fixture = crear({ productoVarianteId: 208, autoAgregarParam: true });

    const req = httpMock.expectOne(`${environment.apiUrl}/carrito/items`);
    req.flush({ items: [], subtotal_seleccionado: 0, fecha_actualizacion: new Date().toISOString() });
    fixture.detectChanges();

    httpMock.expectNone(`${environment.apiUrl}/carrito/items`);
  });

  it('si el agregado automático falla, igual limpia el flag (no reintenta solo)', () => {
    iniciarSesionComoCliente();
    const fixture = crear({ productoVarianteId: 208, autoAgregarParam: true });

    const req = httpMock.expectOne(`${environment.apiUrl}/carrito/items`);
    req.flush(
      { detail: 'No hay disponibilidad suficiente para esa cantidad.' },
      { status: 422, statusText: 'Unprocessable Entity' },
    );
    fixture.detectChanges();

    httpMock.expectNone(`${environment.apiUrl}/carrito/items`);
  });
});
