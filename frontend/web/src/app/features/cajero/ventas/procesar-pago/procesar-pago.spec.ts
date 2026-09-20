import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { environment } from '../../../../../environments/environment';
import { PagoConfirmadoOut, VentaPresencialOut } from '../venta-presencial.model';
import { ProcesarPago } from './procesar-pago';

/**
 * Prueba de regresión para CU25 -- modal "Procesar pago" (ficha flotante,
 * ÚNICO componente de pago, compartido por venta directa y venta desde
 * reserva):
 *  - muestra código VT, (si corresponde) RS, productos y total;
 *  - EFECTIVO: revela monto recibido/cambio, no deja confirmar si el monto
 *    es menor al total, calcula el cambio correctamente;
 *  - TARJETA: exige elegir tipo antes de poder confirmar;
 *  - QR: no exige ningún campo;
 *  - "Confirmar pago" llama a POST /pagos-presenciales/{id}/confirmar con
 *    SOLO los datos de ese método (nunca precios/total) y muestra "Pago
 *    registrado" con lo que devuelve el backend;
 *  - cerrar (X, botón o fondo) emite `cerrar` sin llamar al backend.
 */
describe('ProcesarPago', () => {
  let http: HttpTestingController;

  const venta: VentaPresencialOut = {
    id: 7,
    codigo_venta: 'VT-00007',
    tipo: 'PRESENCIAL',
    estado: 'PENDIENTE_PAGO',
    origen: 'DIRECTA',
    total: 200,
    fecha_creacion: new Date().toISOString(),
    reserva: null,
    detalles: [
      {
        producto: { id: 1, nombre: 'Chompa Andina', imagen_principal_url: null },
        variante: { id: 2, talla: { id: 1, nombre: 'M' }, color: { id: 1, nombre: 'Negro' } },
        cantidad: 1,
        precio_unitario: 200,
        subtotal: 200,
      },
    ],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProcesarPago],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  function crear(v: VentaPresencialOut = venta) {
    const fixture = TestBed.createComponent(ProcesarPago);
    fixture.componentRef.setInput('venta', v);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function botonMetodo(fixture: ReturnType<typeof crear>, texto: string): HTMLButtonElement {
    return Array.from(raiz(fixture).querySelectorAll('.metodo-card')).find(
      (b) => b.textContent?.trim() === texto,
    ) as HTMLButtonElement;
  }

  function botonConfirmar(fixture: ReturnType<typeof crear>): HTMLButtonElement {
    return raiz(fixture).querySelector('.modal-ficha__confirmar') as HTMLButtonElement;
  }

  it('muestra código de venta, productos y total', () => {
    const fixture = crear();
    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('VT-00007');
    expect(texto).toContain('Chompa Andina');
    expect(texto).toContain('Negro');
    expect(texto).toContain('M');
    expect(texto).toContain('200.00');
  });

  it('con reserva, muestra también el código RS', () => {
    const fixture = crear({ ...venta, origen: 'RESERVA', reserva: { codigo_reserva: 'RS-00099', cliente_nombre: 'Ana' } });
    expect(raiz(fixture).textContent).toContain('RS-00099');
  });

  it('EFECTIVO: no deja confirmar con monto menor al total; calcula el cambio; confirma con el monto exacto', () => {
    const fixture = crear();
    botonMetodo(fixture, 'Efectivo').click();
    fixture.detectChanges();

    const input = raiz(fixture).querySelector('.metodo-detalle input[type="number"]') as HTMLInputElement;
    input.value = '150';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(botonConfirmar(fixture).disabled).toBe(true);

    input.value = '250';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(botonConfirmar(fixture).disabled).toBe(false);
    expect(raiz(fixture).querySelector('.campo-monto__valor--cambio')?.textContent).toContain('50.00');

    botonConfirmar(fixture).click();
    const req = http.expectOne(`${environment.apiUrl}/pagos-presenciales/7/confirmar`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ metodo_pago: 'EFECTIVO', monto_recibido: 250 });

    const pago: PagoConfirmadoOut = { codigo_venta: 'VT-00007', total: 200, metodo_pago: 'EFECTIVO', monto_recibido: 250, cambio: 50 };
    req.flush(pago);
    fixture.detectChanges();

    const texto = raiz(fixture).textContent ?? '';
    expect(texto).toContain('Pago registrado');
    expect(texto).toContain('VT-00007');
    expect(texto).toContain('Cambio: Bs 50.00');
  });

  it('TARJETA: exige elegir tipo antes de poder confirmar; envía tipo_tarjeta y referencia', () => {
    const fixture = crear();
    botonMetodo(fixture, 'Tarjeta').click();
    fixture.detectChanges();
    expect(botonConfirmar(fixture).disabled).toBe(true);

    const debito = Array.from(raiz(fixture).querySelectorAll('.opcion-tarjeta')).find((b) =>
      b.textContent?.includes('Débito'),
    ) as HTMLButtonElement;
    debito.click();
    fixture.detectChanges();
    expect(botonConfirmar(fixture).disabled).toBe(false);

    const referencia = raiz(fixture).querySelector('.metodo-detalle input[type="text"]') as HTMLInputElement;
    referencia.value = 'AUTH123';
    referencia.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    botonConfirmar(fixture).click();
    const req = http.expectOne(`${environment.apiUrl}/pagos-presenciales/7/confirmar`);
    expect(req.request.body).toEqual({ metodo_pago: 'TARJETA', tipo_tarjeta: 'DEBITO', referencia: 'AUTH123' });
    req.flush({ codigo_venta: 'VT-00007', total: 200, metodo_pago: 'TARJETA', monto_recibido: null, cambio: null });
  });

  it('QR: no exige ningún campo obligatorio para confirmar', () => {
    const fixture = crear();
    botonMetodo(fixture, 'QR').click();
    fixture.detectChanges();
    expect(botonConfirmar(fixture).disabled).toBe(false);

    botonConfirmar(fixture).click();
    const req = http.expectOne(`${environment.apiUrl}/pagos-presenciales/7/confirmar`);
    expect(req.request.body).toEqual({ metodo_pago: 'QR' });
    req.flush({ codigo_venta: 'VT-00007', total: 200, metodo_pago: 'QR', monto_recibido: null, cambio: null });
  });

  it('cerrar (X) emite "cerrar" sin llamar al backend', () => {
    const fixture = crear();
    const cerrarSpy = vi.fn();
    fixture.componentInstance.cerrar.subscribe(cerrarSpy);

    (raiz(fixture).querySelector('.modal-ficha__cerrar') as HTMLButtonElement).click();

    expect(cerrarSpy).toHaveBeenCalled();
    http.expectNone(`${environment.apiUrl}/pagos-presenciales/7/confirmar`);
  });

  it('clic en el fondo cierra; clic dentro de la ficha NO cierra', () => {
    const fixture = crear();
    const cerrarSpy = vi.fn();
    fixture.componentInstance.cerrar.subscribe(cerrarSpy);

    (raiz(fixture).querySelector('.modal-ficha') as HTMLElement).click();
    expect(cerrarSpy).not.toHaveBeenCalled();

    (raiz(fixture).querySelector('.modal-overlay') as HTMLElement).click();
    expect(cerrarSpy).toHaveBeenCalled();
  });
});
