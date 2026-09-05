import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  LoginResponse,
  RolUsuario,
  Usuario,
} from '../../usuarios-y-accesos/shared/models/usuario.model';

const TOKEN_KEY = 'fashionstore_token';
const USER_KEY = 'fashionstore_usuario';

/**
 * Sesión del usuario autenticado. Es un servicio "core" (global, transversal)
 * porque lo consumen partes del sitio ajenas a usuarios-y-accesos: el header
 * público, el layout admin, los guards y el interceptor HTTP.
 *
 * La lógica exclusiva de CU01 (el formulario y su llamada a /auth/login) vive
 * en usuarios-y-accesos/cu01-iniciar-sesion; este servicio es la pieza
 * reutilizable que también usarán CU02-CU05.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);

  private readonly _usuario = signal<Usuario | null>(this.leerUsuarioAlmacenado());
  private readonly _token = signal<string | null>(this.leerTokenAlmacenado());

  readonly usuario = this._usuario.asReadonly();
  readonly isAuthenticated = computed(() => this._token() !== null);

  login(correo: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${environment.apiUrl}/auth/login`, { correo, password })
      .pipe(tap((response) => this.guardarSesion(response)));
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this._token.set(null);
    this._usuario.set(null);
  }

  hasRole(...roles: RolUsuario[]): boolean {
    const usuario = this._usuario();
    return usuario !== null && roles.includes(usuario.rol);
  }

  getToken(): string | null {
    return this._token();
  }

  private guardarSesion(response: LoginResponse): void {
    localStorage.setItem(TOKEN_KEY, response.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(response.usuario));
    this._token.set(response.access_token);
    this._usuario.set(response.usuario);
  }

  private leerTokenAlmacenado(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }

  private leerUsuarioAlmacenado(): Usuario | null {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? (JSON.parse(raw) as Usuario) : null;
    } catch {
      return null;
    }
  }
}
