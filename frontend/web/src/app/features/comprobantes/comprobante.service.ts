import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ComprobanteVentaOut, EnviarComprobanteOut } from './comprobante.model';

/** Consume CU31 -- Emitir comprobante de venta. Requiere un CLIENTE o un
 * CAJERO autenticado (el interceptor HTTP ya adjunta el Bearer token). El
 * backend resuelve SIEMPRE del token si el actor puede ver esta Venta --
 * este servicio nunca envía cliente_id ni sucursal_id, solo el `venta_id`
 * de la URL. Compartido entre features/cliente/comprobantes y
 * features/cajero/comprobantes -- un único servicio, nunca duplicado. */
@Injectable({ providedIn: 'root' })
export class ComprobanteService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/comprobantes`;

  obtener(ventaId: number): Observable<ComprobanteVentaOut> {
    return this.http.get<ComprobanteVentaOut>(`${this.baseUrl}/${ventaId}`);
  }

  descargarPdf(ventaId: number): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/${ventaId}/pdf`, { responseType: 'blob' });
  }

  enviar(ventaId: number): Observable<EnviarComprobanteOut> {
    return this.http.post<EnviarComprobanteOut>(`${this.baseUrl}/${ventaId}/enviar`, {});
  }
}

/** Dispara la descarga de un Blob ya recibido (PDF del comprobante) con el
 * nombre de archivo dado -- compartido entre el visor de Cliente y el de
 * Cajero, nunca duplicado. */
export function descargarBlob(blob: Blob, nombreArchivo: string): void {
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombreArchivo;
  enlace.click();
  URL.revokeObjectURL(url);
}
