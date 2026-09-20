import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { environment } from '../../../../environments/environment';
import { ResumenCompraOut, SucursalCompraOut, VentaOut } from '../compra-digital.model';
import { FinalizarCompra } from './finalizar-compra';

/**
 * Prueba de regresión para CU22 -- pantalla "Finalizar compra":
 *  - carga el resumen (SOLO lo que ya devuelve el backend, nunca calcula
 *    nada en Angular) y, sin selección, muestra el estado de error con
 *    salida al carrito en vez de romper la pantalla;
 *  - al elegir ciudad, consulta sucursales de CU22 (no la lista pública
 *    simple de CU07) y deshabilita/marca la que no cubre toda la compra;
 *  - si ninguna sucursal cubre la compra, muestra el mensaje exacto pedido
 *    y un botón al carrito;
 *  - "Continuar al pago" llama a POST /compra-digital con SOLO
 *    { sucursal_id } (nunca envía precios/total) y, apenas la Venta queda
 *    creada, navega a /pago/iniciar con su venta_id -- CU22 nunca vuelve a
 *    mostrar el código VT ni ningún estado técnico: el pago (CU23) vive en
 *    su propia carpeta (ver finalizar-compra.ts).
 */
describe('FinalizarCompra', () => {
  let httpMock: HttpTestingController;

  const resumenBase: ResumenCompraOut = {
    items: [
      {
        item_id: 501,
        producto_variante_id: 208,
        producto: { id: 78, nombre: 'Chompa oversize', imagen_principal_url: null },
        variante: { id: 208, talla: { id: 1, nombre: 'M' }, color: { id: 2, nombre: 'Rojo' } },
        precio_unitario: 150,
        precio_base: 150,
        en_promocion: false,
        porcentaje_descuento: null,
      },
    ],
    total: 150,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FinalizarCompra],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  function crear() {
    const fixture = TestBed.createComponent(FinalizarCompra);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function responderCargaInicial(fixture: ReturnType<typeof crear>, resumen: ResumenCompraOut | null): void {
    const reqResumen = httpMock.expectOne(`${environment.apiUrl}/compra-digital/resumen`);
    if (resumen) {
      reqResumen.flush(resumen);
    } else {
      reqResumen.flush({ detail: 'No hay prendas seleccionadas.' }, { status: 422, statusText: 'Unprocessable Entity' });
    }
    const reqCiudades = httpMock.expectOne(`${environment.apiUrl}/sucursales-publicas/ciudades`);
    reqCiudades.flush([{ id: 9, nombre: 'La Paz' }]);
    fixture.detectChanges();
  }

  it('sin prendas seleccionadas, muestra el estado de error con salida al carrito', () => {
    const fixture = crear();
    responderCargaInicial(fixture, null);

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('No hay prendas seleccionadas');
    expect(raiz(fixture).querySelector('a[href="/carrito"]')).not.toBeNull();
  });

  it('con prendas seleccionadas, el paso 1 muestra producto, variante, precio y el total', () => {
    const fixture = crear();
    responderCargaInicial(fixture, resumenBase);

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Chompa oversize');
    expect(texto).toContain('Rojo');
    expect(texto).toContain('M');
    expect(raiz(fixture).querySelector('.compra-resumen__valor')?.textContent).toContain('150.00');
  });

  it('al elegir ciudad, consulta GET /compra-digital/sucursales y marca la que no cubre todo', () => {
    const fixture = crear();
    responderCargaInicial(fixture, resumenBase);

    (raiz(fixture).querySelector('button.paso-siguiente') as HTMLButtonElement).click();
    fixture.detectChanges();

    const select = raiz(fixture).querySelector('select.campo-ciudad__select') as HTMLSelectElement;
    select.value = '9';
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    const req = httpMock.expectOne((r) => r.url === `${environment.apiUrl}/compra-digital/sucursales`);
    expect(req.request.params.get('ciudad_id')).toBe('9');
    const sucursales: SucursalCompraOut[] = [
      { id: 1, nombre: 'Sucursal Full', direccion: 'Av. Uno', disponible_para_compra: true },
      { id: 2, nombre: 'Sucursal Parcial', direccion: 'Av. Dos', disponible_para_compra: false },
    ];
    req.flush(sucursales);
    fixture.detectChanges();

    const tarjetas = Array.from(raiz(fixture).querySelectorAll('.sucursal-card')) as HTMLButtonElement[];
    expect(tarjetas.length).toBe(2);
    expect(tarjetas[0].disabled).toBe(false);
    expect(tarjetas[1].disabled).toBe(true);
    expect(tarjetas[1].textContent).toContain('No disponible para todas las prendas');
  });

  it('si ninguna sucursal cubre la compra, muestra el mensaje exacto y el botón al carrito', () => {
    const fixture = crear();
    responderCargaInicial(fixture, resumenBase);

    (raiz(fixture).querySelector('button.paso-siguiente') as HTMLButtonElement).click();
    fixture.detectChanges();

    const select = raiz(fixture).querySelector('select.campo-ciudad__select') as HTMLSelectElement;
    select.value = '9';
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    const req = httpMock.expectOne((r) => r.url === `${environment.apiUrl}/compra-digital/sucursales`);
    req.flush([{ id: 2, nombre: 'Sucursal Parcial', direccion: 'Av. Dos', disponible_para_compra: false }]);
    fixture.detectChanges();

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('No existe una sucursal con disponibilidad para todas las prendas seleccionadas.');
    expect(raiz(fixture).querySelector('a[href="/carrito"]')).not.toBeNull();
  });

  it('"Continuar al pago" llama a POST /compra-digital con solo { sucursal_id } y navega a /pago/iniciar', () => {
    const fixture = crear();
    responderCargaInicial(fixture, resumenBase);

    (raiz(fixture).querySelector('button.paso-siguiente') as HTMLButtonElement).click();
    fixture.detectChanges();
    const select = raiz(fixture).querySelector('select.campo-ciudad__select') as HTMLSelectElement;
    select.value = '9';
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    httpMock
      .expectOne((r) => r.url === `${environment.apiUrl}/compra-digital/sucursales`)
      .flush([{ id: 1, nombre: 'Sucursal Full', direccion: 'Av. Uno', disponible_para_compra: true }]);
    fixture.detectChanges();

    (raiz(fixture).querySelector('.sucursal-card') as HTMLButtonElement).click();
    fixture.detectChanges();

    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    const botonPrincipal = raiz(fixture).querySelector('.acciones-confirmacion .btn--primary') as HTMLButtonElement;
    expect(botonPrincipal.textContent).toContain('Continuar al pago');
    botonPrincipal.click();
    fixture.detectChanges();

    const req = httpMock.expectOne(`${environment.apiUrl}/compra-digital`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ sucursal_id: 1 });

    const venta: VentaOut = {
      id: 42,
      codigo_venta: 'VT-00001',
      sucursal: { id: 1, nombre: 'Sucursal Full', direccion: 'Av. Uno', ciudad: 'La Paz' },
      tipo: 'DIGITAL',
      estado: 'PENDIENTE_PAGO',
      total: 150,
      fecha_creacion: new Date().toISOString(),
      detalles: [],
    };
    req.flush(venta);
    fixture.detectChanges();

    // CU22 nunca vuelve a mostrar el código VT ni ningún estado técnico --
    // solo entrega el venta_id y navega hacia CU23.
    expect(navigateSpy).toHaveBeenCalledWith(['/pago/iniciar'], { queryParams: { venta_id: 42 } });
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).not.toContain('VT-00001');
    expect(texto).not.toContain('PENDIENTE_PAGO');
  });
});
