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
  is_active?: boolean;
  es_activo?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PlanCrear {
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
}

export interface PlanActualizar {
  nombre?: string;
  descripcion?: string;
  precio?: number;
  limite_sucursales?: number;
  limite_usuarios?: number;
  gestion_productos?: boolean;
  gestion_ventas?: boolean;
  reservas?: boolean;
  operacion_offline?: boolean;
  reportes_convencionales?: boolean;
  reportes_generativos_ia?: boolean;
}

export interface CambiarEstadoPlan {
  is_active: boolean;
}

export interface Empresa {
  id: number;
  nombre: string;
  razon_social: string;
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

  // CU04 — Gestionar Planes SaaS
  getPlanes(): Observable<Plan[]> {
    return this.http.get<Plan[]>(`${this.apiUrl}/planes`);
  }

  getPlan(id: number): Observable<Plan> {
    return this.http.get<Plan>(`${this.apiUrl}/planes/${id}`);
  }

  createPlan(payload: PlanCrear): Observable<Plan> {
    return this.http.post<Plan>(`${this.apiUrl}/planes`, payload);
  }

  updatePlan(id: number, payload: PlanActualizar): Observable<Plan> {
    return this.http.put<Plan>(`${this.apiUrl}/planes/${id}`, payload);
  }

  cambiarEstadoPlan(id: number, payload: CambiarEstadoPlan): Observable<Plan> {
    return this.http.patch<Plan>(`${this.apiUrl}/planes/${id}/estado`, payload);
  }

  deletePlan(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/planes/${id}`);
  }
}
