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
}
