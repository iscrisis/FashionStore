import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { environment } from '../../../../../environments/environment';
import { ProductoBusquedaOut, VentaPresencialOut } from '../venta-presencial.model';
import { VentaDirecta } from './venta-directa';

/**
 * Prueba de regresión para CU24 -- "Nueva venta" (venta directa):
 *  - buscar llama a GET /ventas-presenciales/productos?nombre=...;
 *  - agregar una variante crea una línea; agregarla de nuevo incrementa la
 *    cantidad en vez de duplicar la línea (respetando el disponible);
 *  - "Registrar venta" llama a POST /ventas-presenciales/directa con SOLO
 *    { items: [{producto_variante_id, cantidad}] } (nunca precios/total) y
 *    muestra el resumen con lo que devuelve el backend;
 *  - CU25 -- "Continuar al pago" abre el modal <app-procesar-pago> sobre
 *    esta misma pantalla (nunca navega a otra página).
 */
describe('VentaDirecta', () => {
  let http: HttpTestingController;

  const resultado: ProductoBusquedaOut = {
    producto_variante_id: 55,
    producto: { id: 5, nombre: 'Chompa Andina', imagen_principal_url: null },
    variante: { id: 55, talla: { id: 1, nombre: 'M' }, color: { id: 2, nombre: 'Negro' } },
    precio_unitario: 130,
    en_promocion: false,
    porcentaje_descuento: null,
    disponible: 2,
  };

  beforeEach(async () => {
    localStorage.setItem('fashionstore_token', 'token-de-prueba');
    localStorage.setItem(
      'fashionstore_usuario',
      JSON.stringify({ id: 1, nombre: 'Daniel', correo: 'daniel@fashionstore.com', rol: 'CAJERO' }),
    );
    await TestBed.configureTestingModule({
      imports: [VentaDirecta],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    localStorage.clear();
    http.verify();
  });

  function crear() {
    const fixture = TestBed.createComponent(VentaDirecta);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function buscarYAgregar(fixture: ReturnType<typeof crear>, resultados: ProductoBusquedaOut[] = [resultado]): void {
    const input = raiz(fixture).querySelector('.buscador__input') as HTMLInputElement;
    input.value = 'Chompa';
    input.dispatchEvent(new Event('input'));
    (raiz(fixture).querySelector('.buscador__boton') as HTMLButtonElement).click();

    const req = http.expectOne((r) => r.url === `${environment.apiUrl}/ventas-presenciales/productos`);
    expect(req.request.params.get('nombre')).toBe('Chompa');
    req.flush(resultados);
    fixture.detectChanges();
  }

  it('buscar consulta GET /ventas-presenciales/productos y muestra nombre, variante, stock disponible y precio', () => {
    const fixture = crear();
    buscarYAgregar(fixture);

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Chompa Andina');
    expect(texto).toContain('Negro');
    expect(texto).toContain('M');
    expect(texto).toContain('Stock disponible: 2');
    expect(texto).toContain('130.00');
  });

  it('agregar la misma variante dos veces incrementa la cantidad de la línea, no duplica', () => {
    const fixture = crear();
    buscarYAgregar(fixture);

    const agregar = raiz(fixture).querySelector('.resultado-item button.btn') as HTMLButtonElement;
    agregar.click();
    fixture.detectChanges();
    agregar.click();
    fixture.detectChanges();

    const lineas = raiz(fixture).querySelectorAll('.linea-detalle');
    expect(lineas.length).toBe(1);
    expect(raiz(fixture).querySelector('.cantidad-control__valor')?.textContent).toContain('2');
  });

  it('no permite incrementar más allá del disponible', () => {
    const fixture = crear();
    buscarYAgregar(fixture, [{ ...resultado, disponible: 1 }]);

    (raiz(fixture).querySelector('.resultado-item button.btn') as HTMLButtonElement).click();
    fixture.detectChanges();

    const botonMas = raiz(fixture).querySelector('.cantidad-control__btn[aria-label="Aumentar cantidad"]') as HTMLButtonElement;
    expect(botonMas.disabled).toBe(true);
  });

  it('"Registrar venta" llama a POST /ventas-presenciales/directa con solo producto_variante_id y cantidad, y muestra el resumen', () => {
    const fixture = crear();
    buscarYAgregar(fixture);
    (raiz(fixture).querySelector('.resultado-item button.btn') as HTMLButtonElement).click();
    fixture.detectChanges();

    const registrar = raiz(fixture).querySelector('.detalle-venta__acciones .btn--primary') as HTMLButtonElement;
    expect(registrar.disabled).toBe(false);
    registrar.click();
    fixture.detectChanges();

    const req = http.expectOne(`${environment.apiUrl}/ventas-presenciales/directa`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ items: [{ producto_variante_id: 55, cantidad: 1 }] });

    const venta: VentaPresencialOut = {
      id: 9,
      codigo_venta: 'VT-00009',
      tipo: 'PRESENCIAL',
      estado: 'PENDIENTE_PAGO',
      origen: 'DIRECTA',
      total: 130,
      fecha_creacion: new Date().toISOString(),
      reserva: null,
      detalles: [
        {
          producto: resultado.producto,
          variante: resultado.variante,
          cantidad: 1,
          precio_unitario: 130,
          subtotal: 130,
        },
      ],
    };
    req.flush(venta);
    fixture.detectChanges();

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('VT-00009');
    expect(texto).toContain('130.00');
  });

  it('"Registrar venta" está deshabilitado sin ninguna línea agregada', () => {
    const fixture = crear();
    const registrar = raiz(fixture).querySelector('.detalle-venta__acciones .btn--primary') as HTMLButtonElement;
    expect(registrar.disabled).toBe(true);
  });

  it('CU25 -- "Continuar al pago" abre el modal de procesar-pago con la venta ya registrada', () => {
    const fixture = crear();
    buscarYAgregar(fixture);
    (raiz(fixture).querySelector('.resultado-item button.btn') as HTMLButtonElement).click();
    fixture.detectChanges();
    (raiz(fixture).querySelector('.detalle-venta__acciones .btn--primary') as HTMLButtonElement).click();
    fixture.detectChanges();

    const venta: VentaPresencialOut = {
      id: 9,
      codigo_venta: 'VT-00009',
      tipo: 'PRESENCIAL',
      estado: 'PENDIENTE_PAGO',
      origen: 'DIRECTA',
      total: 130,
      fecha_creacion: new Date().toISOString(),
      reserva: null,
      detalles: [
        { producto: resultado.producto, variante: resultado.variante, cantidad: 1, precio_unitario: 130, subtotal: 130 },
      ],
    };
    http.expectOne(`${environment.apiUrl}/ventas-presenciales/directa`).flush(venta);
    fixture.detectChanges();

    expect(raiz(fixture).querySelector('app-procesar-pago')).toBeNull();

    const continuar = Array.from(raiz(fixture).querySelectorAll('button')).find((b) =>
      b.textContent?.includes('Continuar al pago'),
    ) as HTMLButtonElement;
    continuar.click();
    fixture.detectChanges();

    expect(raiz(fixture).querySelector('app-procesar-pago')).not.toBeNull();
    expect(raiz(fixture).querySelectorAll('.modal-overlay').length).toBe(1);
  });
});
