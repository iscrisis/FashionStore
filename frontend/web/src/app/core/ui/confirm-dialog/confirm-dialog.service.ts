import { Injectable, signal } from '@angular/core';

export interface ConfirmDialogConfig {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
}

@Injectable({ providedIn: 'root' })
export class ConfirmDialogService {
  private readonly _config = signal<ConfirmDialogConfig | null>(null);
  readonly config = this._config.asReadonly();

  private resolver: ((result: boolean) => void) | null = null;

  confirm(config: ConfirmDialogConfig): Promise<boolean> {
    this._config.set(config);
    return new Promise<boolean>((resolve) => {
      this.resolver = resolve;
    });
  }

  resolve(result: boolean): void {
    this._config.set(null);
    this.resolver?.(result);
    this.resolver = null;
  }
}
