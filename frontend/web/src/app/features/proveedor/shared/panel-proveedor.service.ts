import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ColeccionResumen,
  MiProveedor,
  MiProveedorPayload,
  ProductoProveedor,
  ProductoProveedorPayload,
  TemporadaResumen,
} from './panel-proveedor.model';

@Injectable({ providedIn: 'root' })
export class PanelProveedorService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/proveedores/panel`;

  miPerfil(): Observable<MiProveedor> {
    return this.http.get<MiProveedor>(`${this.baseUrl}/perfil`);
  }

  actualizarMiPerfil(payload: MiProveedorPayload): Observable<MiProveedor> {
    return this.http.put<MiProveedor>(`${this.baseUrl}/perfil`, payload);
  }

  temporadas(): Observable<TemporadaResumen[]> {
    return this.http.get<TemporadaResumen[]>(`${this.baseUrl}/temporadas`);
  }

  colecciones(temporadaId: number): Observable<ColeccionResumen[]> {
    const params = new HttpParams().set('temporada_id', temporadaId);
    return this.http.get<ColeccionResumen[]>(`${this.baseUrl}/colecciones`, { params });
  }

  misProductos(): Observable<ProductoProveedor[]> {
    return this.http.get<ProductoProveedor[]>(`${this.baseUrl}/productos`);
  }

  obtenerProducto(id: number): Observable<ProductoProveedor> {
    return this.http.get<ProductoProveedor>(`${this.baseUrl}/productos/${id}`);
  }

  enviarProducto(payload: ProductoProveedorPayload): Observable<ProductoProveedor> {
    return this.http.post<ProductoProveedor>(`${this.baseUrl}/productos`, payload);
  }

  actualizarProducto(id: number, payload: ProductoProveedorPayload): Observable<ProductoProveedor> {
    return this.http.put<ProductoProveedor>(`${this.baseUrl}/productos/${id}`, payload);
  }

  cambiarDisponibilidad(id: number, disponibilidad: boolean): Observable<ProductoProveedor> {
    return this.http.patch<ProductoProveedor>(`${this.baseUrl}/productos/${id}/disponibilidad`, {
      disponibilidad,
    });
  }

  cambiarEstado(id: number, isActive: boolean): Observable<ProductoProveedor> {
    return this.http.patch<ProductoProveedor>(`${this.baseUrl}/productos/${id}/estado`, {
      is_active: isActive,
    });
  }
}
