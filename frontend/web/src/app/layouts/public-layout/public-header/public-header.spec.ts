import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { RolUsuario } from '../../../usuarios-y-accesos/shared/models/usuario.model';
import { PublicHeader } from './public-header';

/**
 * Prueba de regresión para CU18 -- Regla del navbar del cliente: "Mis
 * reservas" debe aparecer en el menú de cuenta (junto a "Mi perfil" y
 * "Cerrar sesión") SOLO para un Cliente autenticado, nunca para otros roles
 * ni para un visitante sin sesión -- este mismo header lo comparten todos
 * los roles que usan el layout público (ver destinoCuenta en public-header.ts).
 *
 * También cubre la corrección del problema de acceso de CAJERO: si un rol
 * interno llega a mostrarse en este header (p. ej. navegó manualmente a una
 * URL pública), "Mi cuenta" debe llevarlo de vuelta a SU propio panel, nunca
 * a '/' -- antes CAJERO y PROVEEDOR no estaban contemplados y caían ahí.
 */
describe('PublicHeader', () => {
  function iniciarSesionComo(rol: RolUsuario): void {
    localStorage.setItem('fashionstore_token', 'token-de-prueba');
    localStorage.setItem(
      'fashionstore_usuario',
      JSON.stringify({ id: 1, nombre: 'Gabriela', correo: 'gabriela@fashionstore.com', rol }),
    );
  }

  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  async function crear() {
    await TestBed.configureTestingModule({
      imports: [PublicHeader],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    const fixture = TestBed.createComponent(PublicHeader);
    fixture.detectChanges();
    return fixture;
  }

  it('sin sesión, el menú de cuenta ni siquiera se muestra (no hay "Mis reservas")', async () => {
    const fixture = await crear();
    const raiz = fixture.nativeElement as HTMLElement;
    expect(raiz.querySelector('.account-menu')).toBeNull();
  });

  it('un CLIENTE autenticado ve "Mis reservas" en su menú de cuenta', async () => {
    iniciarSesionComo('CLIENTE');
    const fixture = await crear();
    const raiz = fixture.nativeElement as HTMLElement;

    fixture.componentInstance.toggleAccountMenu(new MouseEvent('click'));
    fixture.detectChanges();

    const items = Array.from(raiz.querySelectorAll('.account-menu__item')) as HTMLElement[];
    expect(items.some((item) => item.textContent?.trim() === 'Mis reservas')).toBe(true);
  });

  it('un ADMINISTRADOR autenticado NO ve "Mis reservas" en su menú', async () => {
    iniciarSesionComo('ADMINISTRADOR');
    const fixture = await crear();
    const raiz = fixture.nativeElement as HTMLElement;

    fixture.componentInstance.toggleAccountMenu(new MouseEvent('click'));
    fixture.detectChanges();

    const items = Array.from(raiz.querySelectorAll('.account-menu__item')) as HTMLElement[];
    expect(items.some((item) => item.textContent?.trim() === 'Mis reservas')).toBe(false);
  });

  it('un CAJERO autenticado tiene "Mi cuenta" apuntando a /cajero, no a /', async () => {
    iniciarSesionComo('CAJERO');
    const fixture = await crear();
    const raiz = fixture.nativeElement as HTMLElement;

    fixture.componentInstance.toggleAccountMenu(new MouseEvent('click'));
    fixture.detectChanges();

    const enlaceCuenta = raiz.querySelector('.account-menu__item') as HTMLAnchorElement;
    expect(enlaceCuenta.getAttribute('href')).toBe('/cajero');
  });

  it('un PROVEEDOR autenticado tiene "Mi cuenta" apuntando a /proveedor, no a /', async () => {
    iniciarSesionComo('PROVEEDOR');
    const fixture = await crear();
    const raiz = fixture.nativeElement as HTMLElement;

    fixture.componentInstance.toggleAccountMenu(new MouseEvent('click'));
    fixture.detectChanges();

    const enlaceCuenta = raiz.querySelector('.account-menu__item') as HTMLAnchorElement;
    expect(enlaceCuenta.getAttribute('href')).toBe('/proveedor');
  });

  /**
   * Regresión CU21 -- el ícono de carrito (bolsa) ya existía en este header;
   * solo se le agregó el click hacia /carrito, sin tocar el ícono ni
   * agregar contador/badge nuevo (cartCount sigue fijo en 0 a propósito).
   */
  it('sin sesión, el ícono de carrito redirige a /login con returnUrl hacia /carrito', async () => {
    const fixture = await crear();
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    const botonCarrito = (fixture.nativeElement as HTMLElement).querySelector(
      'button.icon-btn[aria-label="Carrito"]',
    ) as HTMLButtonElement;
    botonCarrito.click();

    expect(navigateSpy).toHaveBeenCalledWith(['/login'], { queryParams: { returnUrl: '/carrito' } });
  });

  it('con sesión (CLIENTE), el ícono de carrito navega directo a /carrito', async () => {
    iniciarSesionComo('CLIENTE');
    const fixture = await crear();
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);

    const botonCarrito = (fixture.nativeElement as HTMLElement).querySelector(
      'button.icon-btn[aria-label="Carrito"]',
    ) as HTMLButtonElement;
    botonCarrito.click();

    expect(navigateSpy).toHaveBeenCalledWith('/carrito');
  });

  it('el ícono de carrito nunca muestra contador/badge (cartCount se mantiene en 0)', async () => {
    iniciarSesionComo('CLIENTE');
    const fixture = await crear();
    const raiz = fixture.nativeElement as HTMLElement;
    expect(raiz.querySelector('.icon-btn__badge')).toBeNull();
  });
});
