import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ProductoInventario, SucursalDelEncargado } from './panel-encargado.model';

@Injectable({ providedIn: 'root' })
export class PanelEncargadoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/stock-sucursal/panel`;

  miSucursal(): Observable<SucursalDelEncargado> {
    return this.http.get<SucursalDelEncargado>(`${this.baseUrl}/mi-sucursal`);
  }

  listarInventario(search?: string): Observable<ProductoInventario[]> {
    let params = new HttpParams();
    if (search) {
      params = params.set('search', search);
    }
    return this.http.get<ProductoInventario[]>(`${this.baseUrl}/productos`, { params });
  }
}
