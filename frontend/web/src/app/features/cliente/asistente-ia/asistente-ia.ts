import { Component, ElementRef, effect, inject, signal, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Icon } from '../../../core/ui/icon/icon';
import { resolveMediaUrl } from '../../../core/utils/resolve-media-url';
import { MensajeChat, TurnoChat } from './asistente-ia.model';
import { AsistenteIaService } from './asistente-ia.service';

const _SALUDO_INICIAL = '¡Hola! Soy el asistente de FashionStore. ¿Qué estás buscando?';
const _MENSAJE_ERROR_RED =
  'El asistente no está disponible en este momento. Puedes seguir explorando nuestro catálogo.';
// Mismo tope que el backend (ver schemas.MensajeAsistenteRequest.historial) --
// se recorta también acá para no mandar un payload más grande del que el
// backend igualmente va a recortar.
const _MAX_TURNOS_HISTORIAL = 6;

/**
 * CU29 -- Obtener recomendaciones mediante IA (Cliente/Invitado). Botón
 * flotante + panel de chat, integrado directamente en el layout público (ver
 * layouts/public-layout/public-layout.html) -- vive fuera del
 * <router-outlet>, así que la conversación sobrevive mientras el Cliente
 * navega entre catálogo/producto/carrito.
 *
 * Angular NUNCA llama a Gemini -- solo a POST /asistente-ia/mensaje (ver
 * asistente-ia.service.ts). El historial de esta sesión vive SOLO en este
 * signal (`mensajes`), nunca en una tabla propia -- si el Cliente recarga la
 * página, se pierde y vuelve a empezar con el saludo inicial (aceptable para
 * este CU, ver backend/__init__.py).
 *
 * Los productos que trae cada respuesta del asistente son SIEMPRE los que ya
 * validó FastAPI contra PostgreSQL -- "VER" navega al detalle REAL del
 * producto (misma ruta que usa el catálogo), nunca implementa otro detalle
 * ni agrega al carrito desde acá (fuera de alcance de CU29).
 */
@Component({
  selector: 'app-asistente-ia',
  imports: [Icon, RouterLink],
  templateUrl: './asistente-ia.html',
  styleUrl: './asistente-ia.scss',
})
export class AsistenteIa {
  private readonly service = inject(AsistenteIaService);

  protected readonly resolveMediaUrl = resolveMediaUrl;

  protected readonly abierto = signal(false);
  protected readonly enviando = signal(false);
  protected readonly textoInput = signal('');
  protected readonly mensajes = signal<MensajeChat[]>([{ rol: 'asistente', texto: _SALUDO_INICIAL }]);

  private readonly scrollContainer = viewChild<ElementRef<HTMLElement>>('scrollContainer');

  constructor() {
    // Auto-scroll al último mensaje -- se dispara con cualquier cambio de
    // `mensajes` o `enviando` (los "..." de escribiendo también deben quedar
    // visibles). queueMicrotask espera a que Angular ya haya pintado el DOM
    // del nuevo mensaje antes de medir scrollHeight.
    effect(() => {
      this.mensajes();
      this.enviando();
      queueMicrotask(() => {
        const el = this.scrollContainer()?.nativeElement;
        if (el) {
          el.scrollTop = el.scrollHeight;
        }
      });
    });
  }

  alternar(): void {
    this.abierto.update((valor) => !valor);
  }

  cerrar(): void {
    this.abierto.set(false);
  }

  actualizarTexto(valor: string): void {
    this.textoInput.set(valor);
  }

  enviar(): void {
    const texto = this.textoInput().trim();
    if (!texto || this.enviando()) {
      return;
    }

    // Historial ANTES de agregar este mensaje -- son los turnos previos que
    // le dan contexto a Gemini, el mensaje actual va aparte (ver
    // MensajeAsistenteRequest).
    const historial: TurnoChat[] = this.mensajes()
      .slice(-_MAX_TURNOS_HISTORIAL)
      .map((m) => ({ rol: m.rol, texto: m.texto }));

    this.mensajes.update((actuales) => [...actuales, { rol: 'usuario', texto }]);
    this.textoInput.set('');
    this.enviando.set(true);

    this.service.enviarMensaje({ mensaje: texto, historial }).subscribe({
      next: (respuesta) => {
        this.mensajes.update((actuales) => [
          ...actuales,
          { rol: 'asistente', texto: respuesta.respuesta, productos: respuesta.productos },
        ]);
        this.enviando.set(false);
      },
      error: () => {
        this.mensajes.update((actuales) => [...actuales, { rol: 'asistente', texto: _MENSAJE_ERROR_RED }]);
        this.enviando.set(false);
      },
    });
  }

  onSubmit(evento: Event): void {
    evento.preventDefault();
    this.enviar();
  }
}
