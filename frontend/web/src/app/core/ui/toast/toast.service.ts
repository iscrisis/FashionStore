import { Injectable, signal } from '@angular/core';

// "brand" es una confirmación positiva igual que "success" (mismo ícono de
// check, mismo mecanismo), pero con el acento rojo de FashionStore en vez de
// verde -- para casos como CU17 (crear reserva) donde el verde genérico no
// es la identidad visual esperada. No reemplaza a "success": los demás CU
// (CU14/15/16, etc.) siguen usándolo tal cual, sin cambios.
export type ToastType = 'success' | 'error' | 'info' | 'brand';

export interface ToastMessage {
  id: number;
  type: ToastType;
  text: string;
}

const AUTO_DISMISS_MS = 4000;

@Injectable({ providedIn: 'root' })
export class ToastService {
  private readonly _toasts = signal<ToastMessage[]>([]);
  readonly toasts = this._toasts.asReadonly();

  private nextId = 0;

  success(text: string): void {
    this.push('success', text);
  }

  brand(text: string): void {
    this.push('brand', text);
  }

  error(text: string): void {
    this.push('error', text);
  }

  info(text: string): void {
    this.push('info', text);
  }

  dismiss(id: number): void {
    this._toasts.update((list) => list.filter((toast) => toast.id !== id));
  }

  private push(type: ToastType, text: string): void {
    const id = ++this.nextId;
    this._toasts.update((list) => [...list, { id, type, text }]);
    setTimeout(() => this.dismiss(id), AUTO_DISMISS_MS);
  }
}
