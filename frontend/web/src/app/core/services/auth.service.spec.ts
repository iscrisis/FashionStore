import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AuthService } from './auth.service';

/**
 * Prueba de regresión de la integración mínima de CU20 con el rol Cajero:
 * un CAJERO debe mantener su rol después de refrescar la página. AuthService
 * ya hacía esto genéricamente para cualquier rol (lee localStorage en su
 * constructor, ver auth.service.ts) -- esta prueba lo confirma explícitamente
 * para CAJERO, el rol puntual que motivó esta corrección.
 */
describe('AuthService', () => {
  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('CAJERO mantiene su rol después de "refrescar" (una instancia nueva relee el mismo localStorage)', () => {
    localStorage.setItem('fashionstore_token', 'token-de-prueba');
    localStorage.setItem(
      'fashionstore_usuario',
      JSON.stringify({ id: 1, nombre: 'Prueba', correo: 'prueba@fashionstore.com', rol: 'CAJERO' }),
    );

    // Simula un refresh real: el constructor de AuthService vuelve a leer
    // localStorage -- no hay ningún estado en memoria que sobreviva a un F5.
    const auth = TestBed.inject(AuthService);

    expect(auth.isAuthenticated()).toBe(true);
    expect(auth.hasRole('CAJERO')).toBe(true);
    expect(auth.hasRole('CLIENTE')).toBe(false);
    expect(auth.usuario()?.rol).toBe('CAJERO');
  });
});
