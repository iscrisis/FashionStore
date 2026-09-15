import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../../environments/environment';
import { ProductoDisponibilidad } from './disponibilidad.model';

/** Consume la consulta pública de disponibilidad de CU12 -- sin token, apto para Invitado y Cliente. */
@Injectable({ providedIn: 'root' })
export class DisponibilidadService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/disponibilidad`;

  /**
   * El backend de CU12 siempre responde con todas las variantes activas del
   * producto por sucursal (ver ProductoDisponibilidad); no filtra por talla
   * ni color. tallaId/colorId se aceptan y se envían igual -- por si un
   * futuro ajuste del backend los usa para acotar la respuesta -- pero hoy
   * el filtrado real por variante ocurre en el componente sobre `variantes`.
   */
  consultar(
    productoId: number,
    tallaId?: number,
    colorId?: number,
    ciudadId?: number,
  ): Observable<ProductoDisponibilidad> {
    let params = new HttpParams().set('producto_id', productoId);
    if (tallaId) {
      params = params.set('talla_id', tallaId);
    }
    if (colorId) {
      params = params.set('color_id', colorId);
    }
    if (ciudadId) {
      params = params.set('ciudad_id', ciudadId);
    }
    return this.http.get<ProductoDisponibilidad>(this.baseUrl, { params });
  }
}
