import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Empresa {
  id: number;
  nombre: string;
  slug: string;
  is_active: boolean;
  fecha_creacion: string;
}

export interface Administrador {
  id: number;
  nombre: string;
  correo: string;
  rol: string;
  is_active: boolean;
  empresa_id: number;
  created_at: string;
}

export interface ConsultarAdministradorResponse {
  empresa: Empresa;
  administrador: Administrador;
}

export interface ActualizarAdministradorPayload {
  nombre: string;
  correo: string;
  is_active: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class SuperadminService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1';

  getEmpresas(): Observable<Empresa[]> {
    return this.http.get<Empresa[]>(`${this.apiUrl}/empresas`);
  }

  getEmpresa(id: number): Observable<Empresa> {
    return this.http.get<Empresa>(`${this.apiUrl}/empresas/${id}`);
  }

  // CU02 — Gestionar administrador de empresa
  getAdministrador(empresaId: number): Observable<ConsultarAdministradorResponse> {
    return this.http.get<ConsultarAdministradorResponse>(
      `${this.apiUrl}/empresas/${empresaId}/administrador`,
    );
  }

  updateAdministrador(
    empresaId: number,
    payload: ActualizarAdministradorPayload,
  ): Observable<ConsultarAdministradorResponse> {
    return this.http.put<ConsultarAdministradorResponse>(
      `${this.apiUrl}/empresas/${empresaId}/administrador`,
      payload,
    );
  }
}
