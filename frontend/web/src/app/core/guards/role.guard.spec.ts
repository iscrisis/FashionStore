import { TestBed } from '@angular/core/testing';
import { Router, UrlTree, provideRouter } from '@angular/router';
import { roleGuard } from './role.guard';

/**
 * Pruebas de regresión de arquitectura de roles (corrección del acceso de
 * CAJERO): un rol autenticado que no coincide con el que exige la ruta debe
 * ir a '/no-autorizado', NUNCA a '/' -- ese fallback a '/' (el layout
 * público) era indistinguible de la experiencia de un Cliente, sin importar
 * qué rol real tuviera la cuenta.
 */
describe('roleGuard', () => {
  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({ providers: [provideRouter([])] });
  });

  afterEach(() => {
    localStorage.clear();
  });

  function iniciarSesionComo(rol: string): void {
    localStorage.setItem('fashionstore_token', 'token-de-prueba');
    localStorage.setItem(
      'fashionstore_usuario',
      JSON.stringify({ id: 1, nombre: 'Prueba', correo: 'prueba@fashionstore.com', rol }),
    );
  }

  function ejecutar(...rolesPermitidos: string[]): boolean | UrlTree {
    return TestBed.runInInjectionContext(() => (roleGuard(...(rolesPermitidos as any)) as any)());
  }

  function ruta(resultado: boolean | UrlTree): string {
    return TestBed.inject(Router).serializeUrl(resultado as UrlTree);
  }

  it('sin sesión redirige a /login', () => {
    const resultado = ejecutar('CAJERO');
    expect(ruta(resultado)).toBe('/login');
  });

  it('CAJERO autenticado accediendo a una ruta de CAJERO: acceso permitido', () => {
    iniciarSesionComo('CAJERO');
    expect(ejecutar('CAJERO')).toBe(true);
  });

  it('un CLIENTE que intenta entrar a una ruta de CAJERO va a /no-autorizado, NUNCA a /', () => {
    iniciarSesionComo('CLIENTE');
    const resultado = ejecutar('CAJERO');
    expect(ruta(resultado)).toBe('/no-autorizado');
  });

  it('un CAJERO que intenta entrar a una ruta de ENCARGADO_SUCURSAL va a /no-autorizado', () => {
    iniciarSesionComo('CAJERO');
    const resultado = ejecutar('ENCARGADO_SUCURSAL');
    expect(ruta(resultado)).toBe('/no-autorizado');
  });

  it('ENCARGADO_SUCURSAL sigue entrando a su propia ruta', () => {
    iniciarSesionComo('ENCARGADO_SUCURSAL');
    expect(ejecutar('ENCARGADO_SUCURSAL')).toBe(true);
  });

  it('PROVEEDOR sigue entrando a su propia ruta', () => {
    iniciarSesionComo('PROVEEDOR');
    expect(ejecutar('PROVEEDOR')).toBe(true);
  });

  it('ADMINISTRADOR sigue entrando a su propia ruta', () => {
    iniciarSesionComo('ADMINISTRADOR');
    expect(ejecutar('ADMINISTRADOR')).toBe(true);
  });
});
