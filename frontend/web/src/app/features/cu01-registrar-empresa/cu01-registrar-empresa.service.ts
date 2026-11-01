import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Plan {
  id: number;
  nombre: string;
  slug: string;
  descripcion: string;
  precio: number;
  limite_sucursales: number;
  limite_usuarios: number;
  gestion_productos: boolean;
  gestion_ventas: boolean;
  reservas: boolean;
  operacion_offline: boolean;
  reportes_convencionales: boolean;
  reportes_generativos_ia: boolean;
  is_active: boolean;
}

export interface EmpresaRegistro {
  nombre: string;
  slug: string;
  razon_social: string;
  correo: string;
  telefono: string;
  nombre_admin: string;
  correo_admin: string;
  password: string;
  plan_id?: number;
}

export interface EmpresaDatos {
  id: number;
  nombre: string;
  slug: string;
  razon_social: string;
  correo: string;
  telefono: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UsuarioAdministrador {
  id: number;
  nombre: string;
  correo: string;
  rol: string;
  is_active: boolean;
  created_at: string;
}

export interface RegistroEmpresaResponse {
  empresa: EmpresaDatos;
  administrador: UsuarioAdministrador;
}

@Injectable({
  providedIn: 'root',
})
export class RegistrarEmpresaService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/empresas`;
  private readonly planesUrl = `${environment.apiUrl}/planes`;

  registrarEmpresa(datos: EmpresaRegistro): Observable<RegistroEmpresaResponse> {
    return this.http.post<RegistroEmpresaResponse>(this.apiUrl, datos);
  }

  obtenerPlanesActivos(): Observable<Plan[]> {
    return this.http.get<Plan[]>(`${this.planesUrl}/activos`);
  }
}
