import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { MensajeAsistenteRequest, MensajeAsistenteResponse } from './asistente-ia.model';

/** Consume CU29 -- único punto por el que Angular habla con el asistente;
 * nunca llama a Gemini directamente (ver docstring del backend). Apto para
 * Invitado y Cliente: el interceptor global ya adjunta el token cuando hay
 * sesión iniciada (ver core/interceptors/auth.interceptor.ts), sin nada
 * especial que hacer aquí. */
@Injectable({ providedIn: 'root' })
export class AsistenteIaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/asistente-ia`;

  enviarMensaje(payload: MensajeAsistenteRequest): Observable<MensajeAsistenteResponse> {
    return this.http.post<MensajeAsistenteResponse>(`${this.baseUrl}/mensaje`, payload);
  }
}
