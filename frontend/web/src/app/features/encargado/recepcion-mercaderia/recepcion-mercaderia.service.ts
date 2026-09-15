import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ProductoParaRecepcion,
  ProveedorResumen,
  RecepcionOut,
  RegistrarRecepcionPayload,
} from './recepcion-mercaderia.model';

@Injectable({ providedIn: 'root' })
export class RecepcionMercaderiaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/recepciones-mercaderia/panel`;

  listarProveedores(): Observable<ProveedorResumen[]> {
    return this.http.get<ProveedorResumen[]>(`${this.baseUrl}/proveedores`);
  }

  listarProductosDelProveedor(proveedorId: number): Observable<ProductoParaRecepcion[]> {
    return this.http.get<ProductoParaRecepcion[]>(
      `${this.baseUrl}/proveedores/${proveedorId}/productos`,
    );
  }

  registrar(payload: RegistrarRecepcionPayload): Observable<RecepcionOut> {
    return this.http.post<RecepcionOut>(this.baseUrl, payload);
  }
}
