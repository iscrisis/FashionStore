import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { ReservaDetalleOut, ReservaOut } from '../crear-reserva/crear-reserva.model';
import { CancelarReserva } from './cancelar-reserva';

/**
 * Pruebas de CU19 -- Cancelar reserva (Cliente). Cancela UN detalle (una
 * prenda dentro de una reserva) sin afectar al resto:
 *  - el botón "Cancelar" SOLO aparece si esa prenda está PENDIENTE/PREPARADA;
 *  - al presionarlo se abre un modal de confirmación (nunca cancela directo);
 *  - "Volver" cierra el modal SIN llamar al backend;
 *  - "Cancelar prenda" (dentro del modal) sí llama al backend y, al
 *    responder, emite el detalle ya actualizado para que el padre (CU18,
 *    ver mis-reservas.ts) reemplace esa prenda sin recargar la lista.
 */
describe('CancelarReserva', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CancelarReserva],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  function reservaDePrueba(overrides: Partial<ReservaOut> = {}): ReservaOut {
    return {
      id: 1,
      codigo_reserva: 'RS-00001',
      sucursal: { id: 3, nombre: 'Mall Ventura', ciudad: { id: 4, nombre: 'Santa Cruz' } },
      estado_general: 'PENDIENTE',
      fecha_reserva: '2026-09-18',
      hora_inicio: '16:00:00',
      hora_fin: '17:00:00',
      fecha_creacion: '2026-09-10T12:00:00Z',
      detalles: [],
      ...overrides,
    };
  }

  function detalleDePrueba(overrides: Partial<ReservaDetalleOut> = {}): ReservaDetalleOut {
    return {
      id: 42,
      producto: { id: 10, nombre: 'Chaqueta Denim', imagen_principal_url: null },
      variante: { id: 20, talla: { id: 1, nombre: 'M' }, color: { id: 2, nombre: 'Blanco' } },
      cantidad: 1,
      estado: 'PENDIENTE',
      ...overrides,
    };
  }

  function crear(detalle: ReservaDetalleOut, reserva: ReservaOut = reservaDePrueba()) {
    const fixture = TestBed.createComponent(CancelarReserva);
    fixture.componentRef.setInput('reserva', reserva);
    fixture.componentRef.setInput('detalle', detalle);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function botonCancelar(fixture: ReturnType<typeof crear>): HTMLButtonElement | null {
    return raiz(fixture).querySelector('.cancelar-btn');
  }

  it('un detalle PENDIENTE muestra el botón "Cancelar"', () => {
    const fixture = crear(detalleDePrueba({ estado: 'PENDIENTE' }));
    expect(botonCancelar(fixture)).not.toBeNull();
  });

  it('un detalle PREPARADA (CU20) también muestra el botón "Cancelar"', () => {
    const fixture = crear(detalleDePrueba({ estado: 'PREPARADA' }));
    expect(botonCancelar(fixture)).not.toBeNull();
  });

  it('un detalle EN_ATENCION (CU20) ya no puede cancelarse -- no muestra botón', () => {
    const fixture = crear(detalleDePrueba({ estado: 'EN_ATENCION' }));
    expect(botonCancelar(fixture)).toBeNull();
  });

  it('un detalle LISTA_PARA_CAJA (CU20) no muestra ningún botón', () => {
    const fixture = crear(detalleDePrueba({ estado: 'LISTA_PARA_CAJA' }));
    expect(botonCancelar(fixture)).toBeNull();
  });

  it('un detalle VENCIDA (CU20) no muestra ningún botón', () => {
    const fixture = crear(detalleDePrueba({ estado: 'VENCIDA' }));
    expect(botonCancelar(fixture)).toBeNull();
  });

  it('un detalle CANCELADA no muestra ningún botón', () => {
    const fixture = crear(detalleDePrueba({ estado: 'CANCELADA' }));
    expect(botonCancelar(fixture)).toBeNull();
  });

  it('un detalle ATENDIDA no muestra ningún botón', () => {
    const fixture = crear(detalleDePrueba({ estado: 'ATENDIDA' }));
    expect(botonCancelar(fixture)).toBeNull();
  });

  it('al presionar el botón se abre el modal de confirmación (sin cancelar todavía)', () => {
    const fixture = crear(detalleDePrueba());
    expect(raiz(fixture).querySelector('.cancelar-modal-overlay')).toBeNull();

    botonCancelar(fixture)!.click();
    fixture.detectChanges();

    expect(raiz(fixture).querySelector('.cancelar-modal-overlay')).not.toBeNull();
    expect(raiz(fixture).textContent).toContain('¿Deseas cancelar esta prenda?');
    http.expectNone(`${environment.apiUrl}/reservas/detalles/42/cancelar`);
  });

  it('"Volver" cierra el modal sin llamar al backend', () => {
    const fixture = crear(detalleDePrueba());
    botonCancelar(fixture)!.click();
    fixture.detectChanges();

    const volverBtn = raiz(fixture).querySelector('.cancelar-modal__volver') as HTMLButtonElement;
    volverBtn.click();
    fixture.detectChanges();

    expect(raiz(fixture).querySelector('.cancelar-modal-overlay')).toBeNull();
    http.expectNone(`${environment.apiUrl}/reservas/detalles/42/cancelar`);
  });

  it('confirmar llama a PATCH /reservas/detalles/:id/cancelar y emite el detalle actualizado', () => {
    const fixture = crear(detalleDePrueba());
    let emitido: ReservaDetalleOut | undefined;
    fixture.componentInstance.cancelada.subscribe((d) => (emitido = d));

    botonCancelar(fixture)!.click();
    fixture.detectChanges();

    const confirmarBtn = raiz(fixture).querySelector('.cancelar-modal__confirmar') as HTMLButtonElement;
    confirmarBtn.click();

    const req = http.expectOne(`${environment.apiUrl}/reservas/detalles/42/cancelar`);
    expect(req.request.method).toBe('PATCH');
    req.flush(detalleDePrueba({ estado: 'CANCELADA' }));
    fixture.detectChanges();

    expect(emitido?.estado).toBe('CANCELADA');
    expect(raiz(fixture).querySelector('.cancelar-modal-overlay')).toBeNull();
    // Ya no es PENDIENTE -- el botón desaparece con el nuevo input.
    fixture.componentRef.setInput('detalle', detalleDePrueba({ estado: 'CANCELADA' }));
    fixture.detectChanges();
    expect(botonCancelar(fixture)).toBeNull();
  });
});
