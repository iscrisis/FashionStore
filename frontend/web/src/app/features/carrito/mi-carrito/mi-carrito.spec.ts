import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { environment } from '../../../../environments/environment';
import { CarritoItemOut, CarritoOut } from '../carrito.model';
import { MiCarrito } from './mi-carrito';

/**
 * Prueba de regresión para CU21 -- pantalla "Mi carrito" ('/carrito'):
 *  - carrito vacío muestra el estado limpio ("Tu carrito está vacío." +
 *    "Seguir comprando"), nunca una tabla vacía ni un error técnico;
 *  - con items, cada tarjeta muestra imagen/nombre/color/talla/precio y su
 *    selección individual (checkbox) -- SIN control de cantidad;
 *  - dos unidades de la MISMA variante son dos tarjetas independientes: se
 *    puede seleccionar una sin afectar la otra, y eliminar una deja la otra
 *    intacta;
 *  - el resumen muestra "Subtotal seleccionado" solo cuando hay algo
 *    seleccionado, y el mensaje de "selecciona al menos una prenda" cuando
 *    no hay ninguna.
 */
describe('MiCarrito', () => {
  let httpMock: HttpTestingController;

  function item(overrides: Partial<CarritoItemOut>): CarritoItemOut {
    return {
      item_id: 501,
      producto_variante_id: 208,
      producto: { id: 78, nombre: 'Chompa oversize', imagen_principal_url: null },
      variante: { id: 208, talla: { id: 1, nombre: 'M' }, color: { id: 2, nombre: 'Rojo' } },
      precio_unitario: 150,
      precio_base: 150,
      en_promocion: false,
      porcentaje_descuento: null,
      seleccionado: true,
      ...overrides,
    };
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MiCarrito],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  function crear() {
    const fixture = TestBed.createComponent(MiCarrito);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function responder(
    fixture: ReturnType<typeof crear>,
    carrito: CarritoOut,
    method = 'GET',
    url = `${environment.apiUrl}/carrito`,
  ): void {
    const req = httpMock.expectOne(url);
    expect(req.request.method).toBe(method);
    req.flush(carrito);
    fixture.detectChanges();
  }

  it('carrito vacío muestra el estado limpio, sin tabla ni error', () => {
    const fixture = crear();
    responder(fixture, { items: [], subtotal_seleccionado: 0, fecha_actualizacion: new Date().toISOString() });

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Tu carrito está vacío.');
    expect(raiz(fixture).querySelector('a.btn')?.textContent).toContain('Seguir comprando');
    expect(raiz(fixture).querySelector('.state-block--error')).toBeNull();
  });

  it('con items, muestra producto, variante y precio -- sin ningún control de cantidad', () => {
    const fixture = crear();
    responder(fixture, {
      items: [item({})],
      subtotal_seleccionado: 150,
      fecha_actualizacion: new Date().toISOString(),
    });

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Chompa oversize');
    expect(texto).toContain('Rojo');
    expect(texto).toContain('M');
    expect(raiz(fixture).querySelector('.cantidad-control')).toBeNull();
    expect(raiz(fixture).querySelector('.item-carrito__precio')?.textContent).toContain('Precio: Bs 150.00');
    expect(raiz(fixture).querySelector('.carrito-resumen__valor')?.textContent).toContain(
      'Subtotal seleccionado: Bs 150.00',
    );
  });

  it('con algo seleccionado, "CONTINUAR COMPRA" ya lleva a /finalizar-compra (CU22)', () => {
    const fixture = crear();
    responder(fixture, {
      items: [item({})],
      subtotal_seleccionado: 150,
      fecha_actualizacion: new Date().toISOString(),
    });

    const continuar = raiz(fixture).querySelector('.carrito-resumen__continuar') as HTMLAnchorElement;
    expect(continuar.getAttribute('href')).toBe('/finalizar-compra');
  });

  it('un precio_unitario que llega como string (contrato roto) no rompe la pantalla: muestra "--" y lo loguea', () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const fixture = crear();
    responder(fixture, {
      // Simula la regresión real reportada: el backend enviando el monto
      // como string en vez de number -- nunca debería pasar tras el fix de
      // schemas.py, pero la vista debe protegerse igual (ver formatearMonto).
      items: [item({ precio_unitario: '150.00' as unknown as number })],
      subtotal_seleccionado: 150,
      fecha_actualizacion: new Date().toISOString(),
    });

    expect(raiz(fixture).querySelector('.item-carrito__precio')?.textContent).toContain('Precio: Bs --');
    expect(errorSpy).toHaveBeenCalled();
    errorSpy.mockRestore();
  });

  it('dos unidades de la misma variante son dos tarjetas independientes, cada una con su checkbox', () => {
    const fixture = crear();
    responder(fixture, {
      items: [item({ item_id: 501, seleccionado: true }), item({ item_id: 502, seleccionado: false })],
      subtotal_seleccionado: 150,
      fecha_actualizacion: new Date().toISOString(),
    });

    const tarjetas = raiz(fixture).querySelectorAll('.item-carrito');
    expect(tarjetas.length).toBe(2);
    const checkboxes = Array.from(raiz(fixture).querySelectorAll('input[type="checkbox"]')) as HTMLInputElement[];
    expect(checkboxes.map((c) => c.checked)).toEqual([true, false]);
  });

  it('marcar/desmarcar la selección de una tarjeta llama a PATCH con el nuevo valor', () => {
    const fixture = crear();
    responder(fixture, { items: [item({})], subtotal_seleccionado: 150, fecha_actualizacion: new Date().toISOString() });

    const checkbox = raiz(fixture).querySelector('input[type="checkbox"]') as HTMLInputElement;
    checkbox.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    const req = httpMock.expectOne(`${environment.apiUrl}/carrito/items/501`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ seleccionado: false });
    req.flush({ items: [item({ seleccionado: false })], subtotal_seleccionado: 0, fecha_actualizacion: new Date().toISOString() });
  });

  it('sin ninguna prenda seleccionada, muestra el mensaje en vez del subtotal', () => {
    const fixture = crear();
    responder(fixture, {
      items: [item({ seleccionado: false })],
      subtotal_seleccionado: 0,
      fecha_actualizacion: new Date().toISOString(),
    });

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Selecciona una prenda para continuar.');
    expect(raiz(fixture).querySelector('.carrito-resumen__valor')).toBeNull();
  });

  it('"Eliminar" en una unidad llama a DELETE con SU item_id y no afecta la otra', () => {
    const fixture = crear();
    responder(fixture, {
      items: [item({ item_id: 501 }), item({ item_id: 502 })],
      subtotal_seleccionado: 300,
      fecha_actualizacion: new Date().toISOString(),
    });

    const eliminarBtns = raiz(fixture).querySelectorAll('.item-carrito__eliminar');
    (eliminarBtns[0] as HTMLButtonElement).click();
    fixture.detectChanges();

    responder(
      fixture,
      { items: [item({ item_id: 502 })], subtotal_seleccionado: 150, fecha_actualizacion: new Date().toISOString() },
      'DELETE',
      `${environment.apiUrl}/carrito/items/501`,
    );

    const tarjetas = raiz(fixture).querySelectorAll('.item-carrito');
    expect(tarjetas.length).toBe(1);
  });
});
