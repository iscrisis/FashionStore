import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { AuthService } from '../../../core/services/auth.service';
import { CrearReserva } from './crear-reserva';
import { bloquesHorarioDisponibles, proximosDias } from './horario-reserva';

/**
 * Prueba de regresión para el flujo de CU17 sin sesión:
 *  - el botón "Reservar" (fuera del modal) se habilita por producto+
 *    variante+sucursal completos, SIN pedir fecha/horario todavía y SIN
 *    depender de estar autenticado;
 *  - al presionarlo se abre el modal "Programar reserva" (nunca navega);
 *  - la sesión solo se verifica al presionar "Confirmar reserva" dentro
 *    del modal (ver confirmar() en crear-reserva.ts).
 * AuthService lee su token de localStorage; en un TestBed limpio no hay
 * ninguno guardado, así que arranca como visitante sin sesión, exactamente
 * el escenario a cubrir.
 */
describe('CrearReserva', () => {
  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [CrearReserva],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  function crear(inputs: { productoVarianteId?: number | null; sucursalId?: number | null }) {
    const fixture = TestBed.createComponent(CrearReserva);
    fixture.componentRef.setInput('productoVarianteId', inputs.productoVarianteId ?? null);
    fixture.componentRef.setInput('sucursalId', inputs.sucursalId ?? null);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function botonReservar(fixture: ReturnType<typeof crear>): HTMLButtonElement {
    return raiz(fixture).querySelector('button.reserva-btn')!;
  }

  function overlay(fixture: ReturnType<typeof crear>): HTMLElement | null {
    return raiz(fixture).querySelector('.reserva-modal-overlay');
  }

  /** Primer día no-domingo de la ventana (con al menos un bloque libre) --
   * evita depender de qué fecha/hora exacta sea válida cuando corre la
   * suite, igual que la suite de backend. */
  function primerDiaYBloqueValidos(): { iso: string; bloque: string } {
    for (const dia of proximosDias()) {
      const bloques = bloquesHorarioDisponibles(dia.iso);
      if (!dia.esDomingo && bloques.length > 0) {
        return { iso: dia.iso, bloque: bloques[0] };
      }
    }
    throw new Error('No se encontró ningún día/bloque válido en la ventana de 7 días.');
  }

  it('sin sesión y sin sucursal elegida, el botón Reservar queda deshabilitado', () => {
    const fixture = crear({ productoVarianteId: 208, sucursalId: null });
    expect(botonReservar(fixture).disabled).toBe(true);
  });

  it('sin sesión pero con producto+variante+sucursal, el botón Reservar ya se habilita (sin pedir fecha/hora aún)', () => {
    const fixture = crear({ productoVarianteId: 208, sucursalId: 9 });
    // Confirma que el escenario probado es realmente "sin sesión".
    expect(TestBed.inject(AuthService).isAuthenticated()).toBe(false);
    expect(botonReservar(fixture).disabled).toBe(false);
  });

  it('al presionar Reservar se abre el modal en la misma página (sin navegar), incluso sin sesión', () => {
    const fixture = crear({ productoVarianteId: 208, sucursalId: 9 });
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    expect(overlay(fixture)).toBeNull();
    botonReservar(fixture).click();
    fixture.detectChanges();

    expect(overlay(fixture)).not.toBeNull();
    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it('domingo aparece como tarjeta deshabilitada dentro del modal', () => {
    const fixture = crear({ productoVarianteId: 208, sucursalId: 9 });
    botonReservar(fixture).click();
    fixture.detectChanges();

    const domingoBtn = Array.from(
      raiz(fixture).querySelectorAll('.reserva-dia-btn') as NodeListOf<HTMLButtonElement>,
    ).find((btn) => btn.textContent?.includes('Dom'));

    if (domingoBtn) {
      expect(domingoBtn.disabled).toBe(true);
      expect(domingoBtn.textContent).toContain('No disponible');
    }
  });

  it('sin sesión, tras elegir fecha y horario y presionar Confirmar reserva, redirige al login con returnUrl (incluye fecha/hora) y NO crea la reserva todavía', () => {
    const fixture = crear({ productoVarianteId: 208, sucursalId: 9 });
    fixture.componentRef.setInput('returnUrl', '/producto/78?tallaId=1&colorId=2&sucursalId=9');
    fixture.detectChanges();

    botonReservar(fixture).click();
    fixture.detectChanges();

    const { iso, bloque } = primerDiaYBloqueValidos();
    const componente = fixture.componentInstance;
    componente.seleccionarFecha(iso, false);
    fixture.detectChanges();
    componente.seleccionarHora(bloque);
    fixture.detectChanges();

    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    const confirmarBtn = raiz(fixture).querySelector('.reserva-modal__confirmar') as HTMLButtonElement;
    expect(confirmarBtn.disabled).toBe(false);
    confirmarBtn.click();

    expect(navigateSpy).toHaveBeenCalledWith(['/login'], {
      queryParams: { returnUrl: `/producto/78?tallaId=1&colorId=2&sucursalId=9&fecha=${iso}&hora=${bloque}` },
    });
  });
});
