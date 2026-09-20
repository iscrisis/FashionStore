import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { Login } from './login';

/**
 * Pruebas de regresión de CU01 -- corrigen el problema de acceso de CAJERO:
 * después de iniciar sesión, cada rol debe navegar a SU PROPIO destino.
 * Antes, un if/else incompleto en submit() solo contemplaba
 * ADMINISTRADOR/PROVEEDOR/ENCARGADO_SUCURSAL y dejaba cualquier otro rol
 * (incluido CAJERO) caer en un destino '/' por defecto -- el mismo layout
 * público que ve un Cliente. Ahora usa RUTA_POR_ROL (core/utils/ruta-por-rol.ts),
 * un Record exhaustivo de los 5 roles. CAJERO navega a '/cajero' (integración
 * mínima de CU20 -- "Reservas pendientes de atención"), nunca a '/'.
 */
describe('Login', () => {
  let http: HttpTestingController;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Login],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    http.verify();
  });

  function crear() {
    const fixture = TestBed.createComponent(Login);
    fixture.detectChanges();
    return fixture;
  }

  function raiz(fixture: ReturnType<typeof crear>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  /** Completa y envía el formulario real (por el DOM, no tocando el
   * FormGroup interno -- es `protected`) y responde el POST /auth/login con
   * el rol indicado, simulando exactamente lo que hace el backend real. */
  function iniciarSesionComoRol(fixture: ReturnType<typeof crear>, rol: string): void {
    const correoInput = raiz(fixture).querySelector('input[type="email"]') as HTMLInputElement;
    const passwordInput = raiz(fixture).querySelector('input[type="password"]') as HTMLInputElement;
    correoInput.value = 'usuario@fashionstore.com';
    correoInput.dispatchEvent(new Event('input'));
    passwordInput.value = 'ClaveSegura123!';
    passwordInput.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    raiz(fixture).querySelector('form')!.dispatchEvent(new Event('submit'));

    const req = http.expectOne((r) => r.url.endsWith('/auth/login'));
    // `as any`: `rol` es un string genérico a propósito para poder probar
    // también el caso defensivo de un rol que no está en RolUsuario (ver el
    // último test) -- el backend real nunca emite algo fuera de esos 5.
    req.flush({
      access_token: 'token-de-prueba',
      token_type: 'bearer',
      usuario: { id: 1, nombre: 'Prueba', correo: 'usuario@fashionstore.com', rol },
    } as any);
  }

  it('CAJERO navega a /cajero -- antes caía en / y se veía como un Cliente', () => {
    const fixture = crear();
    const navigateSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    iniciarSesionComoRol(fixture, 'CAJERO');
    expect(navigateSpy).toHaveBeenCalledWith('/cajero');
  });

  it('ADMINISTRADOR navega a /admin', () => {
    const fixture = crear();
    const navigateSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    iniciarSesionComoRol(fixture, 'ADMINISTRADOR');
    expect(navigateSpy).toHaveBeenCalledWith('/admin');
  });

  it('ENCARGADO_SUCURSAL navega a /encargado', () => {
    const fixture = crear();
    const navigateSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    iniciarSesionComoRol(fixture, 'ENCARGADO_SUCURSAL');
    expect(navigateSpy).toHaveBeenCalledWith('/encargado');
  });

  it('PROVEEDOR navega a /proveedor', () => {
    const fixture = crear();
    const navigateSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    iniciarSesionComoRol(fixture, 'PROVEEDOR');
    expect(navigateSpy).toHaveBeenCalledWith('/proveedor');
  });

  it('CLIENTE navega al área pública (/)', () => {
    const fixture = crear();
    const navigateSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    iniciarSesionComoRol(fixture, 'CLIENTE');
    expect(navigateSpy).toHaveBeenCalledWith('/');
  });

  it('un rol no reconocido nunca cae a un panel por defecto -- muestra acceso no autorizado', () => {
    const fixture = crear();
    const navigateSpy = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    iniciarSesionComoRol(fixture, 'ROL_INEXISTENTE');
    expect(navigateSpy).toHaveBeenCalledWith('/no-autorizado');
  });
});
