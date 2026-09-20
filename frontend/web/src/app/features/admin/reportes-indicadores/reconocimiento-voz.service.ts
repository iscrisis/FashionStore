import { Injectable } from '@angular/core';

/**
 * CU30 -- segunda parte: comando de voz de la "consulta inteligente".
 * Envoltorio mínimo sobre la API nativa del navegador
 * (SpeechRecognition/webkitSpeechRecognition) -- sin librería nueva (ver
 * instrucciones de CU30: "NO instalar una librería pesada únicamente para
 * reconocimiento de voz").
 *
 * La voz ÚNICAMENTE hace voz -> texto: el texto reconocido se trata luego
 * exactamente igual que si el Administrador lo hubiera escrito (ver
 * reportes.ts) -- nunca se envía audio a ningún backend ni a Gemini.
 *
 * Si el navegador no soporta reconocimiento de voz, `disponible` queda en
 * false -- reportes.ts lo usa para mostrar el aviso correspondiente sin
 * romper el resto de CU30 (el campo de texto siempre sigue disponible).
 */
@Injectable({ providedIn: 'root' })
export class ReconocimientoVozService {
  readonly disponible: boolean;

  private readonly reconocimiento: SpeechRecognitionLike | null;

  constructor() {
    const ventana = window as unknown as {
      SpeechRecognition?: new () => SpeechRecognitionLike;
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    };
    const Constructor = ventana.SpeechRecognition ?? ventana.webkitSpeechRecognition;
    this.disponible = !!Constructor;
    this.reconocimiento = Constructor ? new Constructor() : null;
    if (this.reconocimiento) {
      this.reconocimiento.lang = 'es-ES';
      this.reconocimiento.interimResults = false;
      this.reconocimiento.maxAlternatives = 1;
    }
  }

  /** Escucha un único enunciado y resuelve con el texto reconocido.
   * Rechaza si el navegador no lo soporta, si el Administrador no dio
   * permiso de micrófono, o si terminó sin detectar nada. */
  escuchar(): Promise<string> {
    return new Promise((resolve, reject) => {
      const reconocimiento = this.reconocimiento;
      if (!reconocimiento) {
        reject(new Error('no-disponible'));
        return;
      }

      let resuelto = false;

      reconocimiento.onresult = (evento) => {
        resuelto = true;
        const texto = evento.results?.[0]?.[0]?.transcript ?? '';
        resolve(texto.trim());
      };
      reconocimiento.onerror = (evento) => {
        resuelto = true;
        reject(new Error(evento.error || 'error-reconocimiento'));
      };
      reconocimiento.onend = () => {
        if (!resuelto) {
          reject(new Error('sin-resultado'));
        }
      };

      try {
        reconocimiento.start();
      } catch {
        reject(new Error('no-se-pudo-iniciar'));
      }
    });
  }

  detener(): void {
    this.reconocimiento?.stop();
  }
}

// Forma mínima de la API nativa que este servicio usa -- no es el tipo DOM
// completo (que no todos los lib.dom.ts incluyen todavía), solo lo
// necesario para tipar sin recurrir a `any` en el resto del archivo.
interface SpeechRecognitionResultLike {
  transcript: string;
}

interface SpeechRecognitionEventLike {
  results: ArrayLike<ArrayLike<SpeechRecognitionResultLike>>;
}

interface SpeechRecognitionErrorEventLike {
  error: string;
}

interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((evento: SpeechRecognitionEventLike) => void) | null;
  onerror: ((evento: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}
