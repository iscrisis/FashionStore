import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  MiProveedor,
  MiProveedorPayload,
  ProductoProveedor,
  ProductoProveedorPayload,
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

  establecerImagen(id: number, archivo: File): Observable<ProductoProveedor> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    return this.http.post<ProductoProveedor>(`${this.baseUrl}/productos/${id}/imagen`, formData);
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
